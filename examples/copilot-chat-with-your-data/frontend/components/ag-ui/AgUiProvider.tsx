"use client";

import { HttpAgent } from "@ag-ui/client";
import type { AgentSubscriber } from "@ag-ui/client";
import type { Message } from "@ag-ui/core";
import {
  PropsWithChildren,
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  applyHighlights,
  clearAllHighlights,
  dispatchStrategicCommentaryTab,
  type ChartFocusTarget,
  type HighlightOptions,
} from "../../lib/chart-highlighting";
import { prompt as defaultPrompt } from "../../lib/prompt";
import {
  DataStoryContext,
  type DataStoryAudioSegment,
  type DataStoryState,
  type DataStorySuggestion,
  type DataStoryEvent,
  type DataStoryStep,
} from "../../hooks/useDataStory";

const audioEnv = process.env.NEXT_PUBLIC_DATA_STORY_AUDIO_ENABLED;
const AUDIO_NARRATION_ENABLED =
  !audioEnv || !["false", "0", "no"].includes(audioEnv.toLowerCase());

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  pending?: boolean;
};

export type AgUiContextValue = {
  messages: ChatMessage[];
  isRunning: boolean;
  error: string | null;
  sendMessage: (content: string) => void;
  highlightCharts: (chartIds: string[], options?: HighlightOptions) => void;
};

const AgUiContext = createContext<AgUiContextValue | null>(null);

function generateId(prefix: string) {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Math.random().toString(36).slice(2)}`;
}

type ProviderProps = PropsWithChildren<{
  runtimeUrl: string;
  systemPrompt?: string;
}>;

export function AgUiProvider({ children, runtimeUrl, systemPrompt }: ProviderProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataStoryState, setDataStoryState] = useState<DataStoryState>({
    status: "idle",
    steps: [],
    error: null,
    audioUrl: undefined,
    audioEnabled: AUDIO_NARRATION_ENABLED,
    audioContentType: undefined,
    audioSegments: undefined,
    audioProgress: 0,
    audioGenerationProgress: 0,
    audioGenerationTotalSegments: 0,
    isAnalyzing: false,
    hasTimeline: false,
    activeTalkingPointId: undefined,
  });

  const agentRef = useRef<HttpAgent | null>(null);
  const threadIdRef = useRef<string>(generateId("thread"));
  const historyRef = useRef<Message[]>([]);
  const highlightRegistryRef = useRef<
    Record<
      string,
      {
        chartIds: string[];
        focusTargets: ChartFocusTarget[];
        talkingPoints: Array<{ id: string; chartIds: string[]; focusTargets: ChartFocusTarget[] }>;
        events: DataStoryEvent[];
      }
    >
  >({});
  const storyStepsRef = useRef<DataStoryStep[]>([]);
  const manualAdvanceTimeoutsRef = useRef<number[]>([]);
  const systemMessage = useMemo(() => systemPrompt || defaultPrompt, [systemPrompt]);
  const runtimeBaseUrl = useMemo(() => runtimeUrl.replace(/\/run\/?$/, ""), [runtimeUrl]);

  if (agentRef.current == null) {
    agentRef.current = new HttpAgent({
      url: runtimeUrl,
    });
  }

  const enqueueSuggestion = useCallback((suggestion: DataStorySuggestion) => {
    setDataStoryState((prev) => {
      if (prev.status === "loading" || prev.status === "playing" || prev.status === "awaiting-audio") {
        return prev;
      }
      return {
        ...prev,
        status: "suggested",
        suggestion,
        error: null,
      };
    });
  }, []);

  const dismissSuggestion = useCallback(() => {
    setDataStoryState((prev) => ({
      ...prev,
      status: prev.steps.length ? prev.status : "idle",
      suggestion: undefined,
      error: null,
    }));
  }, []);

  const normaliseFocusTargets = useCallback((raw: unknown): ChartFocusTarget[] => {
    if (!Array.isArray(raw)) {
      return [];
    }
    return raw.reduce<ChartFocusTarget[]>((acc, entry) => {
      if (!entry || typeof entry !== "object") {
        return acc;
      }
      const chartId = typeof (entry as { chartId?: unknown }).chartId === "string"
        ? (entry as { chartId: string }).chartId
        : undefined;
      if (!chartId) {
        return acc;
      }
      const target: ChartFocusTarget = { chartId };
      const source = entry as Record<string, unknown>;
      if (typeof source.seriesIndex === "number") {
        target.seriesIndex = source.seriesIndex;
      }
      if (typeof source.seriesId === "string") {
        target.seriesId = source.seriesId;
      }
      if (typeof source.seriesName === "string") {
        target.seriesName = source.seriesName;
      }
      if (typeof source.dataIndex === "number") {
        target.dataIndex = source.dataIndex;
      }
      if (typeof source.dataName === "string") {
        target.dataName = source.dataName;
      }
      acc.push(target);
      return acc;
    }, []);
  }, []);

  const emitStepEvents = useCallback(
    (stepId: string, { skipHighlight }: { skipHighlight?: boolean } = {}) => {
      const registryEntry = highlightRegistryRef.current[stepId];
      const events = registryEntry?.events ?? [];
      if (!events.length) {
        return;
      }
      events.forEach((event) => {
        if (!event?.name) {
          return;
        }
        if (event.name === "chart.highlight") {
          const value = (event.value ?? {}) as Record<string, unknown>;
          const tabValue = typeof value.tab === "string" ? value.tab : undefined;
          if (tabValue) {
            dispatchStrategicCommentaryTab(tabValue);
          }
          if (!skipHighlight) {
            const ids = Array.isArray(value.chartIds)
              ? (value.chartIds as string[])
              : typeof value.chartId === "string"
                ? [value.chartId as string]
                : [];
            const focusTargets = normaliseFocusTargets(value.focusTargets);
            if (ids.length > 0) {
              applyHighlights(ids, focusTargets.length ? { focusTargets } : undefined);
            }
          }
          return;
        }
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent(event.name, { detail: event.value ?? {} }));
        }
      });
    },
    [normaliseFocusTargets],
  );

  const replayHighlight = useCallback((stepId: string, options?: HighlightOptions) => {
    const registryEntry = highlightRegistryRef.current[stepId];
    const firstTalkingPoint = registryEntry?.talkingPoints?.[0];
    if (firstTalkingPoint) {
      const mergedOptions = firstTalkingPoint.focusTargets.length
        ? { ...(options ?? {}), focusTargets: firstTalkingPoint.focusTargets }
        : options;
      const chartIds = firstTalkingPoint.chartIds.length ? firstTalkingPoint.chartIds : registryEntry?.chartIds ?? [];
      if (chartIds.length > 0) {
        applyHighlights(chartIds, mergedOptions);
      } else {
        applyHighlights([], mergedOptions);
      }
      emitStepEvents(stepId, { skipHighlight: true });
      setDataStoryState((prev) => ({
        ...prev,
        activeStepId: stepId,
        activeTalkingPointId: firstTalkingPoint.id,
      }));
      return;
    }

    const chartIds = registryEntry?.chartIds ?? [];
    const focusTargets = registryEntry?.focusTargets ?? [];
    const mergedOptions = focusTargets.length
      ? { ...(options ?? {}), focusTargets }
      : options;
    if (chartIds.length > 0) {
      applyHighlights(chartIds, mergedOptions);
    } else {
      applyHighlights([], mergedOptions);
    }
    emitStepEvents(stepId, { skipHighlight: true });
    setDataStoryState((prev) => ({
      ...prev,
      activeStepId: stepId,
      activeTalkingPointId: undefined,
    }));
  }, [emitStepEvents]);

  const highlightTalkingPoint = useCallback(
    (stepId: string, talkingPointId: string, options?: HighlightOptions) => {
      const registryEntry = highlightRegistryRef.current[stepId];
      const targetPoint = registryEntry?.talkingPoints?.find((point) => point.id === talkingPointId);
      const fallbackFocus = registryEntry?.focusTargets ?? [];
      const fallbackCharts = registryEntry?.chartIds ?? [];
      const focusTargets = targetPoint?.focusTargets?.length ? targetPoint.focusTargets : fallbackFocus;
      const chartIds = targetPoint?.chartIds?.length ? targetPoint.chartIds : fallbackCharts;
      const mergedOptions = focusTargets.length
        ? { ...(options ?? {}), focusTargets }
        : options;
      if (chartIds.length > 0) {
        applyHighlights(chartIds, mergedOptions);
      } else {
        applyHighlights([], mergedOptions);
      }
      emitStepEvents(stepId, { skipHighlight: true });
      setDataStoryState((prev) => ({
        ...prev,
        activeStepId: stepId,
        activeTalkingPointId: talkingPointId,
      }));
    },
    [emitStepEvents],
  );

  const highlightCharts = useCallback((chartIds: string[], options?: HighlightOptions) => {
    applyHighlights(chartIds, options);
  }, []);

  const clearManualAdvanceTimeouts = useCallback(() => {
    manualAdvanceTimeoutsRef.current.forEach((timeoutId) => {
      window.clearTimeout(timeoutId);
    });
    manualAdvanceTimeoutsRef.current = [];
  }, []);

  const handleTalkingPointPlaybackStart = useCallback(
    (stepId: string, talkingPointId: string) => {
      highlightTalkingPoint(stepId, talkingPointId, { persistent: true });
    },
    [highlightTalkingPoint],
  );

  const handleTalkingPointPlaybackEnd = useCallback((stepId: string, talkingPointId: string) => {
    const registryEntry = highlightRegistryRef.current[stepId];
    const fallbackCharts = registryEntry?.chartIds ?? [];
    const fallbackFocus = registryEntry?.focusTargets ?? [];
    const fallbackOptions = fallbackFocus.length ? { focusTargets: fallbackFocus } : undefined;
    setDataStoryState((prev) => {
      if (prev.activeTalkingPointId !== talkingPointId) {
        return prev;
      }
      if (fallbackCharts.length > 0) {
        applyHighlights(fallbackCharts, fallbackOptions);
      } else {
        applyHighlights([], fallbackOptions);
      }
      return {
        ...prev,
        activeTalkingPointId: undefined,
      };
    });
  }, []);

  const scheduleManualStepProgression = useCallback(
    (steps: DataStoryStep[]) => {
      clearManualAdvanceTimeouts();
      if (!steps.length) {
        return;
      }

      steps.slice(1).forEach((step, index) => {
        const delay = (index + 1) * 2000;
        const timeoutId = window.setTimeout(() => {
          const registryEntry = highlightRegistryRef.current[step.id];
          const firstPoint = registryEntry?.talkingPoints?.[0];
          if (firstPoint) {
            highlightTalkingPoint(step.id, firstPoint.id);
          } else {
            const chartIds = registryEntry?.chartIds ?? [];
            const focusTargets = registryEntry?.focusTargets ?? [];
            const focusOptions = focusTargets.length ? { focusTargets } : undefined;
            if (chartIds.length) {
              applyHighlights(chartIds, focusOptions);
            } else {
              applyHighlights([], focusOptions);
            }
            setDataStoryState((prev) => ({ ...prev, activeTalkingPointId: undefined }));
            setDataStoryState((prev) => ({ ...prev, activeStepId: step.id }));
          }
          emitStepEvents(step.id, { skipHighlight: true });
        }, delay);
        manualAdvanceTimeoutsRef.current.push(timeoutId);
      });

      const completionDelay = steps.length > 1 ? steps.length * 2000 : 500;
      const completionTimeoutId = window.setTimeout(() => {
        setDataStoryState((prev) => ({ ...prev, status: "completed" }));
      }, completionDelay);
      manualAdvanceTimeoutsRef.current.push(completionTimeoutId);
    },
    [clearManualAdvanceTimeouts, emitStepEvents, highlightTalkingPoint],
  );

  const startStory = useCallback(async () => {
    setDataStoryState((prev) => ({
      ...prev,
      status: "loading",
      steps: [],
      error: null,
      audioUrl: undefined,
      audioEnabled: AUDIO_NARRATION_ENABLED,
      audioContentType: undefined,
      audioSegments: undefined,
      audioProgress: 0,
      audioGenerationProgress: 0,
      audioGenerationTotalSegments: 0,
      isAnalyzing: true,
      hasTimeline: false,
      activeTalkingPointId: undefined,
    }));
    clearAllHighlights();
    highlightRegistryRef.current = {};
    storyStepsRef.current = [];
    clearManualAdvanceTimeouts();

    const currentSuggestion = dataStoryState.suggestion;
    if (!currentSuggestion) {
      setDataStoryState((prev) => ({
        ...prev,
        status: prev.status === "loading" ? "idle" : prev.status,
        isAnalyzing: false,
      }));
      return;
    }
    try {
      const response = await fetch(`${runtimeBaseUrl}/action/generateDataStory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intentId: currentSuggestion.intentId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate data story (status ${response.status})`);
      }

      const payload = await response.json();
      const steps: DataStoryStep[] = Array.isArray(payload?.steps) ? payload.steps : [];
      storyStepsRef.current = steps;
      highlightRegistryRef.current = steps.reduce<
        Record<
          string,
          {
            chartIds: string[];
            focusTargets: ChartFocusTarget[];
            talkingPoints: Array<{ id: string; chartIds: string[]; focusTargets: ChartFocusTarget[] }>;
            events: DataStoryEvent[];
          }
        >
      >((acc, step) => {
        const chartIds = Array.isArray(step.chartIds) ? step.chartIds : [];
        const events = Array.isArray(step.agUiEvents)
          ? step.agUiEvents.filter((event): event is DataStoryEvent =>
              Boolean(event && typeof event.name === "string"),
            )
          : [];
        const focusTargets = Array.isArray(step.chartFocus)
          ? normaliseFocusTargets(step.chartFocus)
          : [];
        const talkingPoints = Array.isArray(step.talkingPoints)
          ? step.talkingPoints.map((point) => {
              const pointChartIds = Array.isArray(point.chartIds) ? point.chartIds : [];
              const pointFocusTargets = Array.isArray(point.chartFocus)
                ? normaliseFocusTargets(point.chartFocus)
                : [];
              return {
                id: point.id,
                chartIds: pointChartIds,
                focusTargets: pointFocusTargets,
              };
            })
          : [];
        acc[step.id] = { chartIds, focusTargets, talkingPoints, events };
        return acc;
      }, {});

      if (steps.length === 0) {
        setDataStoryState((prev) => ({
          ...prev,
          status: "completed",
          suggestion: undefined,
          steps: [],
          activeStepId: undefined,
          error: null,
          audioUrl: undefined,
          audioEnabled: false,
          audioContentType: undefined,
          audioSegments: undefined,
          audioProgress: 0,
          audioGenerationProgress: 0,
          audioGenerationTotalSegments: 0,
          isAnalyzing: false,
          hasTimeline: false,
        }));
        storyStepsRef.current = [];
        return;
      }

      setDataStoryState((prev) => ({
        ...prev,
        status: AUDIO_NARRATION_ENABLED ? "awaiting-audio" : "playing",
        suggestion: undefined,
        steps,
        activeStepId: AUDIO_NARRATION_ENABLED ? undefined : steps[0]?.id,
        error: null,
        audioUrl: undefined,
        audioEnabled: AUDIO_NARRATION_ENABLED && steps.length > 0,
        audioContentType: undefined,
        audioSegments: undefined,
        audioProgress: 0,
        audioGenerationProgress: AUDIO_NARRATION_ENABLED ? 0 : prev.audioGenerationProgress ?? 0,
        audioGenerationTotalSegments: AUDIO_NARRATION_ENABLED ? 0 : prev.audioGenerationTotalSegments ?? 0,
        isAnalyzing: false,
        hasTimeline: true,
      }));

      const normalizeSegments = (
        payloadSegments: Array<{ stepId?: unknown; talkingPointId?: unknown; audio?: unknown; contentType?: unknown }>,
      ): DataStoryAudioSegment[] =>
        payloadSegments.reduce<DataStoryAudioSegment[]>((acc, segment) => {
          const stepId = typeof segment?.stepId === "string" ? segment.stepId : undefined;
          const talkingPointId = typeof segment?.talkingPointId === "string" ? segment.talkingPointId : undefined;
          const audioData = typeof segment?.audio === "string" ? segment.audio : undefined;
          if (!stepId || !audioData) {
            return acc;
          }
          const contentType =
            typeof segment?.contentType === "string" && segment.contentType.includes("audio")
              ? segment.contentType
              : "audio/mpeg";
          acc.push({
            stepId,
            talkingPointId,
            url: `data:${contentType};base64,${audioData}`,
            contentType,
          });
          return acc;
        }, []);

      const requestAudio = async (): Promise<{
        segments?: DataStoryAudioSegment[];
        audioUrl?: string;
        contentType?: string;
        error?: string | null;
      }> => {
        if (!AUDIO_NARRATION_ENABLED) {
          return {};
        }

        try {
          const audioResponse = await fetch(`${runtimeBaseUrl}/action/generateDataStoryAudio`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
            body: JSON.stringify({ steps }),
          });

          if (!audioResponse.ok) {
            return {
              error: `Failed to generate audio (status ${audioResponse.status})`,
            };
          }

          const responseContentType = audioResponse.headers.get("content-type") ?? "";
          if (responseContentType.includes("text/event-stream") && audioResponse.body) {
            const reader = audioResponse.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let finalSegments: Array<{ stepId?: unknown; audio?: unknown; contentType?: unknown }> = [];
            let finalAudioBase64: string | undefined;
            let finalContentType: string | undefined;
            let generationError: string | null = null;

            const processEventData = (data: string) => {
              try {
                const event = JSON.parse(data);
                if (!event?.type) {
                  return;
                }

                if (event.type === "STEP_STARTED" && event.stepName === "dataStory.audio") {
                  setDataStoryState((prev) => ({
                    ...prev,
                    status: "awaiting-audio",
                    isAnalyzing: false,
                    audioGenerationProgress: 0,
                  }));
                  return;
                }

                if (event.type === "STEP_FINISHED" && event.stepName === "dataStory.audio") {
                  setDataStoryState((prev) => ({
                    ...prev,
                    audioGenerationProgress: Math.max(prev.audioGenerationProgress ?? 0, 1),
                  }));
                  return;
                }

                if (event.type === "CUSTOM") {
                  if (event.name === "dataStory.audio.lifecycle") {
                    const total = typeof event.value?.totalSegments === "number" ? event.value.totalSegments : 0;
                    setDataStoryState((prev) => ({
                      ...prev,
                      audioGenerationTotalSegments: total,
                    }));
                    return;
                  }

                  if (event.name === "dataStory.audio.progress") {
                    const completed = Number(event.value?.completed ?? 0);
                    const total = Number(event.value?.total ?? 0) || (completed || 1);
                    const progress = total ? Math.min(1, completed / total) : 0;
                    setDataStoryState((prev) => ({
                      ...prev,
                      audioGenerationProgress: Math.max(prev.audioGenerationProgress ?? 0, progress),
                      audioGenerationTotalSegments: total,
                    }));
                    return;
                  }

                  if (event.name === "dataStory.audio.error") {
                    if (!generationError) {
                      const value = event.value ?? {};
                      const candidate =
                        typeof value?.message === "string"
                          ? value.message
                          : typeof value?.code === "string"
                            ? value.code
                            : null;
                      if (candidate) {
                        generationError = candidate;
                      }
                    }
                    return;
                  }

                  if (event.name === "dataStory.audio.complete") {
                    const value = event.value ?? {};
                    if (Array.isArray(value.segments)) {
                      finalSegments = value.segments;
                    }
                    if (typeof value.contentType === "string") {
                      finalContentType = value.contentType;
                    }
                    if (typeof value.audio === "string") {
                      finalAudioBase64 = value.audio;
                    }
                    if (typeof value.error === "string") {
                      generationError = value.error;
                    }
                  }
                }
              } catch (streamErr) {
                console.warn("Failed to parse audio stream event", streamErr);
              }
            };

            while (true) {
              const { value, done } = await reader.read();
              if (done) {
                break;
              }
              buffer += decoder.decode(value, { stream: true });
              let separatorIndex = buffer.indexOf("\n\n");
              while (separatorIndex !== -1) {
                const rawEvent = buffer.slice(0, separatorIndex);
                buffer = buffer.slice(separatorIndex + 2);
                const dataLines = rawEvent
                  .split("\n")
                  .filter((line) => line.startsWith("data:"))
                  .map((line) => line.slice(5).trim());
                if (dataLines.length) {
                  processEventData(dataLines.join(""));
                }
                separatorIndex = buffer.indexOf("\n\n");
              }
            }
            buffer += decoder.decode(new Uint8Array(), { stream: false });
            if (buffer.trim()) {
              const dataLines = buffer
                .split("\n")
                .filter((line) => line.startsWith("data:"))
                .map((line) => line.slice(5).trim());
              if (dataLines.length) {
                processEventData(dataLines.join(""));
              }
            }
            reader.releaseLock();

            const normalizedSegments = normalizeSegments(finalSegments);
            let finalUrl: string | undefined;
            let contentType = finalContentType;

            if ((!contentType || !contentType.includes("audio")) && normalizedSegments[0]?.contentType) {
              contentType = normalizedSegments[0].contentType;
            }

            if (!normalizedSegments.length && finalAudioBase64) {
              const fallbackType = contentType && contentType.includes("audio") ? contentType : "audio/mpeg";
              contentType = fallbackType;
              finalUrl = `data:${fallbackType};base64,${finalAudioBase64}`;
            }

            return {
              segments: normalizedSegments.length ? normalizedSegments : undefined,
              audioUrl: finalUrl,
              contentType,
              error: generationError,
            };
          }

          const audioPayload = await audioResponse.json();
          const payloadSegments = Array.isArray(audioPayload?.segments) ? audioPayload.segments : [];
          const normalizedSegments = normalizeSegments(payloadSegments);

          let audioUrl: string | undefined;
          let contentType =
            typeof audioPayload?.contentType === "string" && audioPayload.contentType.includes("audio")
              ? audioPayload.contentType
              : normalizedSegments[0]?.contentType;

          if (normalizedSegments.length === 0 && typeof audioPayload?.audio === "string") {
            const fallbackType = contentType && contentType.includes("audio") ? contentType : "audio/mpeg";
            contentType = fallbackType;
            audioUrl = `data:${fallbackType};base64,${audioPayload.audio}`;
          }

          return {
            segments: normalizedSegments.length ? normalizedSegments : undefined,
            audioUrl,
            contentType,
            error: typeof audioPayload?.error === "string" ? audioPayload.error : null,
          };
        } catch (audioErr) {
          console.warn("Data story audio generation failed", audioErr);
          return {
            error: audioErr instanceof Error ? audioErr.message : String(audioErr),
          };
        }
      };

      const audioResult = await requestAudio();
      const audioSegments = audioResult.segments;
      const audioUrl = audioResult.audioUrl;
      const audioContentType = audioResult.contentType;
      const audioError = audioResult.error;
      const hasAudio = Boolean((audioSegments && audioSegments.length > 0) || audioUrl);

      if (audioError && !hasAudio) {
        console.warn("Data story audio generation returned an error", audioError);
      }

      const firstStepId = steps[0]?.id;
      setDataStoryState((prev) => ({
        ...prev,
        status: hasAudio ? "awaiting-audio" : "playing",
        steps,
        suggestion: undefined,
        activeStepId: hasAudio ? prev.activeStepId ?? firstStepId : firstStepId,
        audioUrl: hasAudio && audioUrl ? audioUrl : undefined,
        audioEnabled: hasAudio,
        audioContentType: hasAudio ? audioContentType : undefined,
        audioSegments: hasAudio ? audioSegments : undefined,
        audioProgress: hasAudio ? 0 : 1,
        audioGenerationProgress: hasAudio ? Math.max(prev.audioGenerationProgress ?? 0, 1) : 0,
        audioGenerationTotalSegments: hasAudio ? prev.audioGenerationTotalSegments : 0,
        isAnalyzing: false,
        hasTimeline: true,
      }));

      if (hasAudio) {
        // Audio playback handlers will take over progression once narration loads.
      } else {
        if (firstStepId) {
          replayHighlight(firstStepId);
        }
        if (!AUDIO_NARRATION_ENABLED) {
          scheduleManualStepProgression(steps);
        }
      }
    } catch (err) {
      console.error("Data story generation failed", err);
      setDataStoryState((prev) => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : String(err),
        audioEnabled: false,
        audioContentType: undefined,
        audioSegments: undefined,
        audioProgress: 0,
        audioGenerationProgress: 0,
        audioGenerationTotalSegments: 0,
        isAnalyzing: false,
        hasTimeline: false,
      }));
      storyStepsRef.current = [];
    }
  }, [
    dataStoryState.suggestion,
    runtimeBaseUrl,
    clearManualAdvanceTimeouts,
    scheduleManualStepProgression,
    replayHighlight,
    normaliseFocusTargets,
  ]);

  const handleAudioProgress = useCallback(
    (stepId: string) => {
      replayHighlight(stepId, { persistent: true });
      const steps = storyStepsRef.current;
      const total = steps.length;
      if (!total) {
        return;
      }
      const index = steps.findIndex((step) => step.id === stepId);
      if (index === -1) {
        return;
      }
      const progress = Math.min(1, (index + 1) / total);
      setDataStoryState((prev) => ({
        ...prev,
        audioProgress: Math.max(prev.audioProgress ?? 0, progress),
      }));
    },
    [replayHighlight],
  );

  const handleAudioReady = useCallback(() => {
    const steps = storyStepsRef.current;
    if (!steps.length) {
      return;
    }

    setDataStoryState((prev) => {
      if (prev.status === "playing" && prev.activeStepId) {
        return prev;
      }
      const nextActive = prev.activeStepId ?? steps[0]?.id;
      return {
        ...prev,
        status: "playing",
        activeStepId: nextActive,
      };
    });

    const firstStep = steps[0];
    if (firstStep) {
      replayHighlight(firstStep.id, { persistent: true });
      setDataStoryState((prev) => ({ ...prev, audioProgress: steps.length ? 1 / steps.length : 0 }));
    }
  }, [replayHighlight]);

  const handleAudioComplete = useCallback(() => {
    setDataStoryState((prev) => ({ ...prev, status: "completed", audioProgress: 1 }));
    clearManualAdvanceTimeouts();
  }, [clearManualAdvanceTimeouts]);

  const handleAudioAutoplayFailure = useCallback(() => {
    clearManualAdvanceTimeouts();
    const steps = storyStepsRef.current;
    let wasAlreadyDisabled = false;
    setDataStoryState((prev) => {
      if (!prev.audioEnabled) {
        wasAlreadyDisabled = true;
        return prev;
      }
      const nextActive = prev.activeStepId ?? steps[0]?.id;
      return {
        ...prev,
        audioEnabled: false,
        status: steps.length ? "playing" : prev.status,
        activeStepId: nextActive,
        audioProgress: 0,
      };
    });
    if (wasAlreadyDisabled || !steps.length) {
      return;
    }
    const firstStep = steps[0];
    if (firstStep) {
      replayHighlight(firstStep.id);
    }
  }, [clearManualAdvanceTimeouts, replayHighlight]);

  const ensureSystemMessage = useCallback(() => {
    if (!systemMessage) {
      return;
    }
    if (!historyRef.current.some((msg) => msg.role === "system")) {
      historyRef.current = [
        {
          id: "system-message",
          role: "system",
          content: systemMessage,
        },
        ...historyRef.current,
      ];
    }
  }, [systemMessage]);

  const sendMessage = useCallback(
    (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || !agentRef.current) {
        return;
      }
      if (isRunning) {
        return;
      }

      ensureSystemMessage();
      setError(null);

      const userMessageId = generateId("user");
      const userMessage: Message = {
        id: userMessageId,
        role: "user",
        content: trimmed,
      };

      historyRef.current = [...historyRef.current, userMessage];
      setMessages((prev) => [...prev, { id: userMessageId, role: "user", content: trimmed }]);

      const runId = generateId("run");
      const agent = agentRef.current;

      clearAllHighlights();
      setIsRunning(true);

      const subscriber: AgentSubscriber = {
        onRunErrorEvent: ({ event }) => {
          setIsRunning(false);
          setError(event.message ?? "Agent error");
        },
        onRunFinishedEvent: () => {
          setIsRunning(false);
        },
        onTextMessageStartEvent: ({ event }) => {
          const assistantId = event.messageId ?? generateId("assistant");
          const assistantMessage: Message = {
            id: assistantId,
            role: "assistant",
            content: "",
          };
          historyRef.current = [...historyRef.current, assistantMessage];
          setMessages((prev) => [
            ...prev,
            { id: assistantId, role: "assistant", content: "", pending: true },
          ]);
        },
        onTextMessageContentEvent: ({ event, textMessageBuffer }) => {
          const { messageId } = event;
          if (!messageId) return;
          historyRef.current = historyRef.current.map((msg) =>
            msg.id === messageId ? { ...msg, content: textMessageBuffer } : msg,
          );
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, content: textMessageBuffer } : msg,
            ),
          );
        },
        onTextMessageEndEvent: ({ event, textMessageBuffer }) => {
          const { messageId } = event;
          if (!messageId) return;
          historyRef.current = historyRef.current.map((msg) =>
            msg.id === messageId ? { ...msg, content: textMessageBuffer } : msg,
          );
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === messageId ? { ...msg, content: textMessageBuffer, pending: false } : msg,
            ),
          );
        },
        onCustomEvent: ({ event }) => {
          if (event.name === "dataStory.suggestion") {
            const payload = (event.value ?? {}) as Partial<DataStorySuggestion> & { intentId?: string };
            if (payload.intentId && payload.summary) {
              enqueueSuggestion({
                intentId: payload.intentId,
                summary: payload.summary,
                confidence: payload.confidence,
                focusAreas: payload.focusAreas,
              });
            }
            return;
          }

          if (event.name === "chart.highlight") {
            const value = event.value ?? {};
            const ids = Array.isArray(value.chartIds)
              ? value.chartIds
              : value.chartId
                ? [value.chartId]
                : [];
            if (ids.length > 0) {
              applyHighlights(ids);
            }
            const tabValue = typeof value.tab === "string" ? value.tab : undefined;
            if (tabValue) {
              dispatchStrategicCommentaryTab(tabValue);
            }
          }
        },
      };

      agent.threadId = threadIdRef.current;
      agent.messages = historyRef.current;
      agent.state = agent.state ?? {};

      agent
        .runAgent(
          {
            runId,
            tools: [],
            context: [],
            forwardedProps: {},
          },
          subscriber,
        )
        .catch((err) => {
          console.error("AG-UI run error", err);
          setIsRunning(false);
          setError(err?.message ?? String(err));
        });
    },
    [ensureSystemMessage, isRunning, enqueueSuggestion],
  );

  const dataStoryContextValue = useMemo(
    () => ({
      state: dataStoryState,
      dismissSuggestion,
      startStory,
      replayHighlight,
      onAudioReady: handleAudioReady,
      onAudioProgress: handleAudioProgress,
      onAudioComplete: handleAudioComplete,
      onAudioAutoplayFailure: handleAudioAutoplayFailure,
      onTalkingPointStart: handleTalkingPointPlaybackStart,
      onTalkingPointEnd: handleTalkingPointPlaybackEnd,
      audioNarrationEnabled: AUDIO_NARRATION_ENABLED,
    }),
    [
      dataStoryState,
      dismissSuggestion,
      startStory,
      replayHighlight,
      handleAudioReady,
      handleAudioProgress,
      handleAudioComplete,
      handleAudioAutoplayFailure,
      handleTalkingPointPlaybackStart,
      handleTalkingPointPlaybackEnd,
    ],
  );

  return (
    <AgUiContext.Provider value={{ messages, isRunning, error, sendMessage, highlightCharts }}>
      <DataStoryContext.Provider value={dataStoryContextValue}>
        {children}
      </DataStoryContext.Provider>
    </AgUiContext.Provider>
  );
}

export function useAgUiAgent(): AgUiContextValue {
  const ctx = useContext(AgUiContext);
  if (!ctx) {
    throw new Error("useAgUiAgent must be used within an AgUiProvider");
  }
  return ctx;
}
