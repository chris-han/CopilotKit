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
}
export function DataStoryTimeline({ steps, activeStepId, status, onReview, audioUrl, audioEnabled, audioContentType, audioSegments, onAudioStep, onAudioComplete, onAudioAutoplayFailure, onAudioReady }: DataStoryTimelineProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioRefs = useRef<Record<string, HTMLAudioElement | null>>({});
  const stepRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const lastStepIndexRef = useRef<number>(-1);
  const audioReadyNotifiedRef = useRef<boolean>(false);
  const segmentIndexRef = useRef<number>(0);
  const [segmentIndex, setSegmentIndex] = useState<number>(0);
  const [playbackState, setPlaybackState] = useState<"idle" | "playing" | "paused" | "completed">("idle");
  const hasSteps = steps.length > 0;
  const segments = useMemo(
    () => (Array.isArray(audioSegments) ? audioSegments : []),
    [audioSegments],
  );
  const hasSegments = segments.length > 0;
  const segmentMap = useMemo(() => {
    const map = new Map<string, DataStoryAudioSegment>();
    segments.forEach((segment) => {
      if (segment?.stepId) {
        map.set(segment.stepId, segment);
      }
    });
    return map;
  }, [segments]);
  const hasAnyAudio = hasSegments || Boolean(audioUrl);

  const notifyAudioReady = useCallback(() => {
    if (audioReadyNotifiedRef.current) {
      return;
    }
    audioReadyNotifiedRef.current = true;
    onAudioReady?.();
  }, [onAudioReady]);

  useEffect(() => {
    segmentIndexRef.current = segmentIndex;
  }, [segmentIndex]);

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

  const getSegmentForIndex = useCallback(
    (index: number) => {
      if (!hasSegments || steps.length === 0) {
        return undefined;
      }
      const clamped = Math.min(Math.max(index, 0), steps.length - 1);
      const targetStepId = steps[clamped]?.id;
      if (!targetStepId) {
        return undefined;
      }
      return segmentMap.get(targetStepId);
    },
    [hasSegments, segmentMap, steps],
  );

  const findNextSegmentIndex = useCallback(
    (startIndex: number) => {
      if (!hasSegments) {
        return -1;
      }
      for (let idx = Math.max(startIndex, 0); idx < steps.length; idx += 1) {
        const stepId = steps[idx]?.id;
        if (stepId && segmentMap.has(stepId)) {
          return idx;
        }
      }
      return -1;
    },
    [hasSegments, steps, segmentMap],
  );

  const pauseOtherSegments = useCallback((activeStepId: string) => {
    Object.entries(audioRefs.current).forEach(([stepId, element]) => {
      if (!element || stepId === activeStepId) {
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
      const targetSegment = getSegmentForIndex(nextIndex);
      const targetId = targetSegment?.stepId;
      if (!targetId) {
        return;
      }
      const targetAudio = audioRefs.current[targetId];
      if (!targetAudio) {
        return;
      }

      segmentIndexRef.current = nextIndex;
      setSegmentIndex(nextIndex);
      lastStepIndexRef.current = nextIndex;
      setPlaybackState("playing");

      pauseOtherSegments(targetId);

      const playPromise = targetAudio.play();
      if (playPromise?.catch) {
        playPromise.catch(() => {
          if (!options?.userInitiated) {
            onAudioAutoplayFailure?.();
          }
        });
      }
    },
    [findNextSegmentIndex, getSegmentForIndex, hasSegments, onAudioAutoplayFailure, pauseOtherSegments],
  );

  const handleSegmentPlay = useCallback(
    (stepId: string, index: number) => {
      pauseOtherSegments(stepId);
      segmentIndexRef.current = index;
      setSegmentIndex(index);
      lastStepIndexRef.current = index;
      setPlaybackState("playing");
      notifyAudioReady();
      onAudioStep?.(stepId);
    },
    [notifyAudioReady, onAudioStep, pauseOtherSegments],
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
    (stepId: string, index: number) => {
      if (!hasSegments || !audioEnabled) {
        return;
      }
      if (segmentIndexRef.current !== index) {
        return;
      }
      const audio = audioRefs.current[stepId];
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
    (index: number) => {
      if (!hasSegments) {
        setPlaybackState("completed");
        onAudioComplete?.();
        return;
      }
      const nextIndex = findNextSegmentIndex(index + 1);
      if (audioEnabled && nextIndex !== -1) {
        playSegment(nextIndex);
      } else {
        setPlaybackState("completed");
        onAudioComplete?.();
      }
    },
    [hasSegments, findNextSegmentIndex, audioEnabled, playSegment, onAudioComplete],
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
        if (!segmentMap.has(stepId)) {
          return;
        }
        const segmentAudio = audioRefs.current[stepId];
        const isCurrent = segmentIndexRef.current === index && playbackState === "playing";
        if (isCurrent && segmentAudio && !segmentAudio.paused) {
          segmentAudio.pause();
          setPlaybackState("paused");
          return;
        }
        playSegment(index, { userInitiated: true });
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
      segmentMap,
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
        const currentSegment = getSegmentForIndex(segmentIndexRef.current);
        const stepId = currentSegment?.stepId;
        if (stepId) {
          const element = audioRefs.current[stepId];
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
    getSegmentForIndex,
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
            className={`w-16 rounded-full border border-border px-3 py-1 text-xs font-medium transition disabled:opacity-60 ${
              isGlobalControlDisabled
                ? "cursor-not-allowed bg-muted text-muted-foreground"
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
          const isCurrentSegment = hasSegments && segmentIndex === index;
          const stepControlLabel =
            hasSegments
              ? isCurrentSegment && playbackState === "playing"
                ? "Pause"
                : "Play"
              : playbackState === "playing"
                ? "Pause"
                : "Play";
          const stepButtonClasses = `text-xs font-medium transition ${
            isCurrentSegment && playbackState === "playing"
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
                <div className="prose prose-sm mt-2 text-muted-foreground dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdownTables(step.markdown)}</ReactMarkdown>
                </div>
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
                {segment ? (
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
                      onPlay={() => handleSegmentPlay(step.id, index)}
                      onPause={(event) => handleSegmentPause(index, event.currentTarget)}
                      onLoadedData={() => handleSegmentLoaded(step.id, index)}
                      onEnded={() => handleSegmentEnded(index)}
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
