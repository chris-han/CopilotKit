"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { normalizeMarkdownTables } from "../../lib/markdown";
import type {
  DataStoryAudioSegment,
  DataStoryStep,
  DataStoryStatus,
} from "../../hooks/useDataStory";

interface DataStoryTimelineProps {
  steps: DataStoryStep[];
  activeStepId?: string;
  status: DataStoryStatus;
  onReview: (stepId: string) => void;
  audioUrl?: string;
  audioEnabled?: boolean;
  audioContentType?: string;
  audioSegments?: DataStoryAudioSegment[];
  onAudioStep?: (stepId: string) => void;
  onAudioComplete?: () => void;
  onAudioAutoplayFailure?: () => void;
  onAudioReady?: () => void;
  activeTalkingPointId?: string;
  onTalkingPointStart?: (stepId: string, talkingPointId: string) => void;
  onTalkingPointEnd?: (stepId: string, talkingPointId: string) => void;
}
export function DataStoryTimeline({ steps, activeStepId, status, onReview, audioUrl, audioEnabled, audioContentType, audioSegments, onAudioStep, onAudioComplete, onAudioAutoplayFailure, onAudioReady, activeTalkingPointId, onTalkingPointStart, onTalkingPointEnd }: DataStoryTimelineProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioRefs = useRef<Record<string, HTMLAudioElement | null>>({});
  const stepRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const lastStepIndexRef = useRef<number>(-1);
  const currentSegmentStepRef = useRef<string | null>(null);
  const audioReadyNotifiedRef = useRef<boolean>(false);
  const segmentIndexRef = useRef<number>(0);
  const [segmentIndex, setSegmentIndex] = useState<number>(0);
  const [playbackState, setPlaybackState] = useState<"idle" | "playing" | "paused" | "completed">("idle");
  const hasSteps = steps.length > 0;
  const segments = useMemo(
    () => (Array.isArray(audioSegments) ? audioSegments.filter((segment) => Boolean(segment?.stepId)) : []),
    [audioSegments],
  );
  const segmentLookup = useMemo(() => {
    const map = new Map<string, DataStoryAudioSegment>();
    segments.forEach((segment) => {
      if (!segment?.stepId) {
        return;
      }
      const key = segment.talkingPointId
        ? `${segment.stepId}:${segment.talkingPointId}`
        : segment.stepId;
      if (!map.has(key)) {
        map.set(key, segment);
      }
    });
    return map;
  }, [segments]);
  const orderedSegments = useMemo(() => {
    if (!steps.length && segmentLookup.size === 0) {
      return [] as Array<{ key: string; segment: DataStoryAudioSegment }>;
    }
    const entries: Array<{ key: string; segment: DataStoryAudioSegment }> = [];
    const added = new Set<string>();

    steps.forEach((step) => {
      const stepId = step.id;
      const talkingPoints = Array.isArray(step.talkingPoints) ? step.talkingPoints : [];
      if (talkingPoints.length) {
        talkingPoints.forEach((point) => {
          const key = `${stepId}:${point.id}`;
          const segment = segmentLookup.get(key);
          if (segment && !added.has(key)) {
            entries.push({ key, segment });
            added.add(key);
          }
        });
      }
      if (!talkingPoints.length) {
        const key = stepId;
        const segment = segmentLookup.get(key);
        if (segment && !added.has(key)) {
          entries.push({ key, segment });
          added.add(key);
        }
      }
    });

    segmentLookup.forEach((segment, key) => {
      if (!added.has(key)) {
        entries.push({ key, segment });
        added.add(key);
      }
    });

    return entries;
  }, [segmentLookup, steps]);
  const hasStepSegments = orderedSegments.some((entry) => !entry.segment.talkingPointId);
  const hasTalkingPointSegments = orderedSegments.some((entry) => Boolean(entry.segment.talkingPointId));
  const segmentMap = useMemo(() => {
    const map = new Map<string, DataStoryAudioSegment>();
    orderedSegments.forEach(({ segment }) => {
      if (segment?.stepId && !segment?.talkingPointId) {
        map.set(segment.stepId, segment);
      }
    });
    return map;
  }, [orderedSegments]);
  const talkingPointSegmentMap = useMemo(() => {
    const map = new Map<string, Map<string, DataStoryAudioSegment>>();
    orderedSegments.forEach(({ segment }) => {
      if (!segment?.stepId || !segment?.talkingPointId) {
        return;
      }
      const existing = map.get(segment.stepId) ?? new Map<string, DataStoryAudioSegment>();
      existing.set(segment.talkingPointId, segment);
      map.set(segment.stepId, existing);
    });
    return map;
  }, [orderedSegments]);
  const segmentOrderMap = useMemo(() => {
    const map = new Map<string, number>();
    orderedSegments.forEach(({ key, segment }, idx) => {
      if (!segment?.stepId) {
        return;
      }
      map.set(key, idx);
    });
    return map;
  }, [orderedSegments]);
  const stepFirstSegmentMap = useMemo(() => {
    const map = new Map<string, number>();
    orderedSegments.forEach(({ segment }, idx) => {
      const stepId = segment.stepId;
      if (!stepId || map.has(stepId)) {
        return;
      }
      map.set(stepId, idx);
    });
    return map;
  }, [orderedSegments]);
  const effectiveSegmentIndex = orderedSegments.length
    ? Math.min(segmentIndex, orderedSegments.length - 1)
    : 0;
  const activeSegmentEntry = orderedSegments.length ? orderedSegments[effectiveSegmentIndex] : undefined;
  const activeSegmentStepId = activeSegmentEntry?.segment?.stepId;
  const activeSegmentTalkingPointId = activeSegmentEntry?.segment?.talkingPointId;
  const hasAnyAudio = hasStepSegments || hasTalkingPointSegments || Boolean(audioUrl);
  const hasSegments = orderedSegments.length > 0;
  const notifyAudioReady = useCallback(() => {
    if (audioReadyNotifiedRef.current) {
      return;
    }
    audioReadyNotifiedRef.current = true;
    onAudioReady?.();
  }, [onAudioReady]);

  useEffect(() => {
    segmentIndexRef.current = effectiveSegmentIndex;
  }, [effectiveSegmentIndex]);

  useEffect(() => {
    setPlaybackState("idle");
  }, [hasSegments, audioUrl, steps.length]);

  useEffect(() => {
    if (status === "completed") {
      setPlaybackState("completed");
    } else if (status === "loading" || status === "awaiting-audio") {
      setPlaybackState("idle");
    }
  }, [status]);

  useEffect(() => {
    if (!hasSegments) {
      return;
    }
    segmentIndexRef.current = 0;
    setSegmentIndex(0);
    lastStepIndexRef.current = -1;
    audioReadyNotifiedRef.current = false;
    currentSegmentStepRef.current = null;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      audio.load();
    }
  }, [hasSegments, segments.length, steps.length]);

  useEffect(() => {
    if (hasSegments) {
      return;
    }
    segmentIndexRef.current = 0;
    setSegmentIndex(0);
    lastStepIndexRef.current = -1;
    audioReadyNotifiedRef.current = false;
    currentSegmentStepRef.current = null;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
  }, [audioUrl, steps.length, hasSegments]);

  useEffect(() => {
    if (hasSegments) {
      return;
    }
    if (!audioUrl || !hasSteps) {
      return;
    }
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handlePlay = () => {
      if (!hasSteps) {
        return;
      }
      setPlaybackState("playing");
      notifyAudioReady();
      if (lastStepIndexRef.current === -1 && steps[0]) {
        lastStepIndexRef.current = 0;
        onAudioStep?.(steps[0].id);
      }
    };

    const handlePause = () => {
      if (audio.ended) {
        return;
      }
      setPlaybackState("paused");
    };

    const handleTimeUpdate = () => {
      if (!hasSteps || !Number.isFinite(audio.duration) || audio.duration <= 0) {
        return;
      }
      const ratio = Math.max(0, audio.currentTime / audio.duration);
      let index = Math.floor(ratio * steps.length);
      if (index >= steps.length) {
        index = steps.length - 1;
      }
      if (index !== lastStepIndexRef.current && index >= 0) {
        lastStepIndexRef.current = index;
        onAudioStep?.(steps[index].id);
      }
    };

    const handleEnded = () => {
      if (hasSteps) {
        lastStepIndexRef.current = steps.length - 1;
        onAudioStep?.(steps[steps.length - 1].id);
      }
      setPlaybackState("completed");
      onAudioComplete?.();
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    let readyHandler: (() => void) | null = null;
    const attemptPlay = () => {
      if (!audioEnabled) {
        return;
      }
      setPlaybackState("playing");
      notifyAudioReady();
      audio
        .play()
        .catch(() => {
          setPlaybackState("paused");
          onAudioAutoplayFailure?.();
        });
    };

    if (audioEnabled) {
      if (audio.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
        attemptPlay();
      } else {
        readyHandler = () => {
          audio.removeEventListener("canplaythrough", readyHandler!);
          audio.removeEventListener("loadeddata", readyHandler!);
          attemptPlay();
        };
        audio.addEventListener("canplaythrough", readyHandler);
        audio.addEventListener("loadeddata", readyHandler);
      }
    }

    return () => {
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      if (readyHandler) {
        audio.removeEventListener("canplaythrough", readyHandler);
        audio.removeEventListener("loadeddata", readyHandler);
      }
    };
  }, [
    hasSegments,
    audioEnabled,
    audioUrl,
    steps,
    hasSteps,
    notifyAudioReady,
    onAudioStep,
    onAudioComplete,
    onAudioAutoplayFailure,
  ]);

  const getSegmentEntry = useCallback(
    (index: number) => {
      if (!hasSegments || orderedSegments.length === 0) {
        return undefined;
      }
      const clamped = Math.min(Math.max(index, 0), orderedSegments.length - 1);
      return orderedSegments[clamped];
    },
    [hasSegments, orderedSegments],
  );

  const findNextSegmentIndex = useCallback(
    (startIndex: number) => {
      if (!hasSegments) {
        return -1;
      }
      for (let idx = Math.max(startIndex, 0); idx < orderedSegments.length; idx += 1) {
        const entry = orderedSegments[idx];
        if (!entry?.segment?.stepId) {
          continue;
        }
        return idx;
      }
      return -1;
    },
    [hasSegments, orderedSegments],
  );

  const pauseOtherSegments = useCallback((activeKey: string) => {
    Object.entries(audioRefs.current).forEach(([key, element]) => {
      if (!element || key === activeKey) {
        return;
      }
      element.pause();
      element.currentTime = 0;
    });
  }, []);

  const playSegment = useCallback(
    (index: number, options?: { userInitiated?: boolean }) => {
      if (!hasSegments) {
        return;
      }
      const nextIndex = findNextSegmentIndex(index);
      if (nextIndex === -1) {
        return;
      }
      const segmentEntry = getSegmentEntry(nextIndex);
      const targetSegment = segmentEntry?.segment;
      const targetId = targetSegment?.stepId;
      const segmentKey = segmentEntry?.key;
      if (!targetId || !segmentKey) {
        return;
      }
      const targetAudio = audioRefs.current[segmentKey];
      if (!targetAudio) {
        return;
      }

      segmentIndexRef.current = nextIndex;
      setSegmentIndex(nextIndex);
      lastStepIndexRef.current = nextIndex;
      setPlaybackState("playing");

      pauseOtherSegments(segmentKey);

      const playPromise = targetAudio.play();
      if (playPromise?.catch) {
        playPromise.catch(() => {
          if (!options?.userInitiated) {
            onAudioAutoplayFailure?.();
          }
        });
      }
    },
    [findNextSegmentIndex, getSegmentEntry, hasSegments, onAudioAutoplayFailure, pauseOtherSegments],
  );

  const handleSegmentPlay = useCallback(
    (segmentKey: string, index: number, stepId: string, talkingPointId?: string) => {
      pauseOtherSegments(segmentKey);
      segmentIndexRef.current = index;
      setSegmentIndex(index);
      lastStepIndexRef.current = index;
      setPlaybackState("playing");
      notifyAudioReady();

      const previousStepId = currentSegmentStepRef.current;
      const stepChanged = stepId && previousStepId !== stepId;
      if (stepId) {
        if (stepChanged) {
          currentSegmentStepRef.current = stepId;
          onAudioStep?.(stepId);
        } else if (!talkingPointId) {
          onAudioStep?.(stepId);
        }
      } else {
        currentSegmentStepRef.current = null;
      }

      if (talkingPointId) {
        onTalkingPointStart?.(stepId, talkingPointId);
      }
    },
    [notifyAudioReady, onAudioStep, onTalkingPointStart, pauseOtherSegments],
  );

  const handleSegmentPause = useCallback(
    (index: number, element: HTMLAudioElement) => {
      if (segmentIndexRef.current !== index) {
        return;
      }
      if (element.ended) {
        return;
      }
      setPlaybackState("paused");
    },
    [],
  );

  const handleSegmentLoaded = useCallback(
    (segmentKey: string, index: number) => {
      if (!hasSegments || !audioEnabled) {
        return;
      }
      if (segmentIndexRef.current !== index) {
        return;
      }
      const audio = audioRefs.current[segmentKey];
      if (!audio) {
        return;
      }
      if (!audio.paused && audio.currentTime > 0) {
        return;
      }
      const playPromise = audio.play();
      if (playPromise?.catch) {
        playPromise.catch(() => {
          onAudioAutoplayFailure?.();
        });
      }
    },
    [hasSegments, audioEnabled, onAudioAutoplayFailure],
  );

  const handleSegmentEnded = useCallback(
    (index: number, stepId?: string, talkingPointId?: string) => {
      let nextIndex = -1;
      if (!hasSegments) {
        setPlaybackState("completed");
        onAudioComplete?.();
      } else {
        nextIndex = findNextSegmentIndex(index + 1);
        if (audioEnabled && nextIndex !== -1) {
          playSegment(nextIndex);
        } else {
          setPlaybackState("completed");
          onAudioComplete?.();
        }
      }
      if (talkingPointId && stepId) {
        onTalkingPointEnd?.(stepId, talkingPointId);
      }
      if (!audioEnabled || nextIndex === -1) {
        currentSegmentStepRef.current = null;
      }
    },
    [hasSegments, findNextSegmentIndex, audioEnabled, playSegment, onAudioComplete, onTalkingPointEnd],
  );

  useEffect(() => {
    if (!hasSegments || !audioEnabled || audioReadyNotifiedRef.current) {
      return;
    }
    playSegment(segmentIndexRef.current);
  }, [hasSegments, audioEnabled, playSegment]);

  const handleReviewClick = useCallback(
    (stepId: string, index: number) => {
      onReview(stepId);
      if (hasSegments) {
        const targetIndex = stepFirstSegmentMap.get(stepId);
        if (targetIndex === undefined) {
          return;
        }
        const segmentEntry = getSegmentEntry(targetIndex);
        if (!segmentEntry) {
          return;
        }
        const segmentAudio = audioRefs.current[segmentEntry.key];
        const isCurrent = segmentIndexRef.current === targetIndex && playbackState === "playing";
        if (isCurrent && segmentAudio && !segmentAudio.paused) {
          segmentAudio.pause();
          setPlaybackState("paused");
          return;
        }
        playSegment(targetIndex, { userInitiated: true });
        return;
      }
      if (!hasSegments && audioUrl) {
        const audio = audioRef.current;
        if (!audio) {
          return;
        }
        const isCurrent = lastStepIndexRef.current === index && playbackState === "playing";
        if (isCurrent && !audio.paused) {
          audio.pause();
          setPlaybackState("paused");
        }
      }
    },
    [
      onReview,
      hasSegments,
      stepFirstSegmentMap,
      getSegmentEntry,
      playbackState,
      playSegment,
      audioUrl,
    ],
  );

  const handleGlobalControlClick = useCallback(() => {
    if (!hasAnyAudio) {
      return;
    }

    if (playbackState === "playing") {
      if (hasSegments) {
        const currentEntry = getSegmentEntry(segmentIndexRef.current);
        if (currentEntry) {
          const element = audioRefs.current[currentEntry.key];
          element?.pause();
        }
      } else {
        const audio = audioRef.current;
        audio?.pause();
      }
      setPlaybackState("paused");
      return;
    }

    if (hasSegments) {
      const targetIndex = playbackState === "completed" ? 0 : segmentIndexRef.current;
      if (playbackState === "completed") {
        lastStepIndexRef.current = -1;
      }
      playSegment(targetIndex, { userInitiated: true });
      return;
    }

    const audio = audioRef.current;
    if (!audio || !audioUrl) {
      return;
    }
    if (playbackState === "completed") {
      audio.currentTime = 0;
      lastStepIndexRef.current = -1;
    }
    const playPromise = audio.play();
    if (playPromise?.then) {
      playPromise
        .then(() => {
          setPlaybackState("playing");
          notifyAudioReady();
          if (lastStepIndexRef.current === -1 && steps[0]) {
            lastStepIndexRef.current = 0;
            onAudioStep?.(steps[0].id);
          }
        })
        .catch(() => {
          setPlaybackState("paused");
          onAudioAutoplayFailure?.();
        });
    }
  }, [
    hasAnyAudio,
    playbackState,
    hasSegments,
    getSegmentEntry,
    playSegment,
    audioUrl,
    notifyAudioReady,
    onAudioStep,
    onAudioAutoplayFailure,
    steps,
  ]);

  const controlLabel = playbackState === "playing" ? "Pause" : playbackState === "completed" ? "Replay" : "Play";
  const isGlobalControlDisabled = !hasAnyAudio || status === "loading" || status === "awaiting-audio";

  useEffect(() => {
    if (!activeStepId) {
      return;
    }
    const element = stepRefs.current[activeStepId];
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeStepId]);

  useEffect(() => {
    const existingIds = new Set(steps.map((step) => step.id));
    Object.keys(stepRefs.current).forEach((key) => {
      if (!existingIds.has(key)) {
        delete stepRefs.current[key];
      }
    });
  }, [steps]);

  if (!hasSteps) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground">Data Story Timeline</h4>
        {hasAnyAudio ? (
          <button
            type="button"
            onClick={handleGlobalControlClick}
            disabled={isGlobalControlDisabled}
            className={`w-16 cursor-pointer rounded-full border border-border px-3 py-1 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
              isGlobalControlDisabled
                ? "bg-muted text-muted-foreground"
                : "bg-muted text-foreground hover:bg-muted/80"
            }`}
            aria-label={`${controlLabel} narration`}
          >
            {controlLabel}
          </button>
        ) : null}
      </div>
      {audioUrl && !hasSegments ? (
        <div className="mb-4">
          <audio ref={audioRef} controls className="w-full" preload="auto">
            <source src={audioUrl} type={audioContentType ?? "audio/mpeg"} />
            Your browser does not support the audio element.
          </audio>
        </div>
      ) : null}
      <ol className="space-y-4 border-l border-border pl-4">
        {steps.map((step, index) => {
          const isActive = step.id === activeStepId;
          const segment = hasSegments ? segmentMap.get(step.id) : undefined;
          const stepSegmentOrder = typeof segment !== "undefined" ? segmentOrderMap.get(step.id) ?? -1 : -1;
          const isStepActive = hasSegments
            ? activeSegmentStepId === step.id
            : playbackState === "playing" && lastStepIndexRef.current === index;
          const talkingPoints = step.talkingPoints ?? [];
          const talkingPointSegments = talkingPointSegmentMap.get(step.id);
          const hasStepAudio = hasSegments && stepSegmentOrder >= 0 && Boolean(segment);
          const stepControlLabel =
            hasSegments
              ? isStepActive && playbackState === "playing"
                ? "Pause"
                : "Play"
              : playbackState === "playing" && lastStepIndexRef.current === index
                ? "Pause"
                : "Play";
          const stepButtonClasses = `cursor-pointer text-xs font-medium transition ${
            isStepActive && playbackState === "playing"
              ? "text-primary"
              : "text-primary/80 hover:text-primary"
          }`;
          return (
            <li key={step.id} className="relative">
              <span
                className={`absolute -left-2 top-1.5 flex h-3 w-3 -translate-x-1/2 rounded-full ${
                  isActive ? "bg-primary" : "bg-muted"
                }`}
              />
              <div
                className="rounded-xl border border-primary/30 bg-card/95 p-4 text-card-foreground shadow-md ring-1 ring-primary/10"
                ref={(element) => {
                  if (element) {
                    stepRefs.current[step.id] = element;
                  } else {
                    delete stepRefs.current[step.id];
                  }
                }}
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-primary/70">Step {index + 1}</p>
                    <h5 className="text-sm font-semibold text-foreground">{step.title}</h5>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleReviewClick(step.id, index)}
                    className={stepButtonClasses}
                  >
                    {stepControlLabel}
                  </button>
                </div>
                {talkingPoints.length ? (
                  <div className="mt-2 space-y-3 text-sm leading-relaxed text-muted-foreground">
                    {talkingPoints.map((point, pointIndex) => {
                      const pointText = normalizeMarkdownTables(point.markdown);
                      const isActivePoint =
                        (typeof activeSegmentTalkingPointId === "string" &&
                          activeSegmentTalkingPointId === point.id) ||
                        (!activeSegmentTalkingPointId && activeTalkingPointId === point.id);
                      const talkingSegment = talkingPointSegments?.get(point.id);
                      const segmentKey = `${step.id}:${point.id}`;
                      const segmentOrder = segmentOrderMap.get(segmentKey) ?? -1;
                      const hasAudio = Boolean(talkingSegment && segmentOrder >= 0);
                      return (
                        <div key={point.id} className="flex flex-col gap-2">
                          <div className="flex flex-col gap-1">
                            <span
                              className={`text-[11px] font-semibold uppercase tracking-wide ${
                                isActivePoint ? "text-primary" : "text-primary/70"
                              }`}
                            >
                              Sub-step {index + 1}.{pointIndex + 1}
                            </span>
                            <div
                              className={
                                isActivePoint
                                  ? "text-foreground underline decoration-2 decoration-primary"
                                  : "text-muted-foreground"
                              }
                            >
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{pointText}</ReactMarkdown>
                            </div>
                          </div>
                          {hasAudio ? (
                            <audio
                              controls
                              preload="auto"
                              ref={(element) => {
                                if (element) {
                                  audioRefs.current[segmentKey] = element;
                                } else {
                                  delete audioRefs.current[segmentKey];
                                }
                              }}
                              onPlay={() => {
                                handleSegmentPlay(segmentKey, segmentOrder, step.id, point.id);
                              }}
                              onPause={(event) => handleSegmentPause(segmentOrder, event.currentTarget)}
                              onEnded={() => handleSegmentEnded(segmentOrder, step.id, point.id)}
                            >
                              <source src={talkingSegment.url} type={talkingSegment.contentType ?? "audio/mpeg"} />
                              Your browser does not support the audio element.
                            </audio>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="prose prose-sm mt-2 text-muted-foreground dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdownTables(step.markdown)}</ReactMarkdown>
                  </div>
                )}
                {step.kpis?.length ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {step.kpis.map((kpi) => (
                      <div
                        key={`${step.id}-${kpi.label}`}
                        className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2"
                      >
                        <p className="text-xs text-primary/70">{kpi.label}</p>
                        <p className="text-sm font-semibold text-foreground">{kpi.value}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
                {hasStepAudio ? (
                  <div className="mt-3">
                    <audio
                      controls
                      preload="auto"
                      ref={(element) => {
                        if (element) {
                          audioRefs.current[step.id] = element;
                        } else {
                          delete audioRefs.current[step.id];
                        }
                      }}
                      onPlay={() => handleSegmentPlay(step.id, stepSegmentOrder, step.id)}
                      onPause={(event) => handleSegmentPause(stepSegmentOrder, event.currentTarget)}
                      onLoadedData={() => handleSegmentLoaded(step.id, stepSegmentOrder)}
                      onEnded={() => handleSegmentEnded(stepSegmentOrder, step.id)}
                    >
                      <source src={segment.url} type={segment.contentType ?? "audio/mpeg"} />
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
