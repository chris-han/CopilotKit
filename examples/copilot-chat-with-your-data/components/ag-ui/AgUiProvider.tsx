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

import { applyHighlights, clearAllHighlights } from "../../lib/chart-highlighting";
import { prompt as defaultPrompt } from "../../lib/prompt";
import {
  DataStoryContext,
  type DataStoryState,
  type DataStorySuggestion,
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
  });

  const agentRef = useRef<HttpAgent | null>(null);
  const threadIdRef = useRef<string>(generateId("thread"));
  const historyRef = useRef<Message[]>([]);
  const highlightRegistryRef = useRef<Record<string, string[]>>({});
  const systemMessage = useMemo(() => systemPrompt || defaultPrompt, [systemPrompt]);
  const runtimeBaseUrl = useMemo(() => runtimeUrl.replace(/\/run\/?$/, ""), [runtimeUrl]);

  if (agentRef.current == null) {
    agentRef.current = new HttpAgent({
      url: runtimeUrl,
    });
  }

  const enqueueSuggestion = useCallback((suggestion: DataStorySuggestion) => {
    setDataStoryState((prev) => {
      if (prev.status === "loading" || prev.status === "playing") {
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

  const replayHighlight = useCallback((stepId: string) => {
    const chartIds = highlightRegistryRef.current[stepId] ?? [];
    if (chartIds.length > 0) {
      applyHighlights(chartIds);
    }
    setDataStoryState((prev) => ({
      ...prev,
      activeStepId: stepId,
    }));
  }, []);

  const startStory = useCallback(async () => {
    setDataStoryState((prev) => ({
      ...prev,
      status: "loading",
      steps: [],
      error: null,
      audioUrl: undefined,
      audioEnabled: AUDIO_NARRATION_ENABLED,
    }));
    highlightRegistryRef.current = {};

    const currentSuggestion = dataStoryState.suggestion;
    if (!currentSuggestion) {
      setDataStoryState((prev) => ({ ...prev, status: prev.status === "loading" ? "idle" : prev.status }));
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
      highlightRegistryRef.current = steps.reduce<Record<string, string[]>>((acc, step) => {
        acc[step.id] = Array.isArray(step.chartIds) ? step.chartIds : [];
        return acc;
      }, {});

      let audioUrl: string | undefined;
      let hasAudio = false;

      if (AUDIO_NARRATION_ENABLED && steps.length > 0) {
        try {
          const audioResponse = await fetch(`${runtimeBaseUrl}/action/generateDataStoryAudio`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ steps }),
          });
          if (audioResponse.ok) {
            const audioPayload = await audioResponse.json();
            if (audioPayload?.audio) {
              audioUrl = `data:audio/mpeg;base64,${audioPayload.audio}`;
              hasAudio = true;
            }
          }
        } catch (audioErr) {
          console.error("Data story audio generation failed", audioErr);
        }
      }

      const firstStepId = steps[0]?.id;

      setDataStoryState({
        status: steps.length ? "playing" : "completed",
        suggestion: undefined,
        steps,
        activeStepId: firstStepId,
        error: null,
        audioUrl: hasAudio ? audioUrl : undefined,
        audioEnabled: hasAudio,
      });

      if (steps.length > 0) {
        const firstIds = steps[0].chartIds ?? [];
        if (firstIds.length > 0) {
          applyHighlights(firstIds);
        }

        if (!hasAudio) {
          steps.slice(1).forEach((step, index) => {
            if (!step.chartIds?.length) {
              return;
            }
            const delay = (index + 1) * 2000;
            window.setTimeout(() => {
              applyHighlights(step.chartIds);
              setDataStoryState((prev) => ({ ...prev, activeStepId: step.id }));
            }, delay);
          });

          const completionDelay = steps.length > 1 ? steps.length * 2000 : 500;
          window.setTimeout(() => {
            setDataStoryState((prev) => ({ ...prev, status: "completed" }));
          }, completionDelay);
        }
      } else {
        setDataStoryState((prev) => ({ ...prev, status: "completed", audioEnabled: false }));
      }
    } catch (err) {
      console.error("Data story generation failed", err);
      setDataStoryState((prev) => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : String(err),
        audioEnabled: false,
      }));
    }
  }, [dataStoryState.suggestion, runtimeBaseUrl]);

  const handleAudioProgress = useCallback(
    (stepId: string) => {
      replayHighlight(stepId);
    },
    [replayHighlight],
  );

  const handleAudioComplete = useCallback(() => {
    setDataStoryState((prev) => ({ ...prev, status: "completed" }));
  }, []);

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
    [ensureSystemMessage, isRunning],
  );

  const dataStoryContextValue = useMemo(
    () => ({
      state: dataStoryState,
      dismissSuggestion,
      startStory,
      replayHighlight,
      onAudioProgress: handleAudioProgress,
      onAudioComplete: handleAudioComplete,
      audioNarrationEnabled: AUDIO_NARRATION_ENABLED,
    }),
    [
      dataStoryState,
      dismissSuggestion,
      startStory,
      replayHighlight,
      handleAudioProgress,
      handleAudioComplete,
    ],
  );

  return (
    <AgUiContext.Provider value={{ messages, isRunning, error, sendMessage }}>
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
