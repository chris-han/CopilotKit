"use client";

import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { normalizeMarkdownTables } from "../../lib/markdown";
import type { DataStoryStep, DataStoryStatus } from "../../hooks/useDataStory";

interface DataStoryTimelineProps {
  steps: DataStoryStep[];
  activeStepId?: string;
  status: DataStoryStatus;
  onReview: (stepId: string) => void;
  audioUrl?: string;
  audioEnabled?: boolean;
  audioContentType?: string;
  onAudioStep?: (stepId: string) => void;
  onAudioComplete?: () => void;
  onAudioAutoplayFailure?: () => void;
}

export function DataStoryTimeline({ steps, activeStepId, status, onReview, audioUrl, audioEnabled, audioContentType, onAudioStep, onAudioComplete, onAudioAutoplayFailure }: DataStoryTimelineProps) {
  if (!steps.length) {
    return null;
  }

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastStepIndexRef = useRef<number>(-1);

  useEffect(() => {
    lastStepIndexRef.current = -1;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
  }, [audioUrl, steps.length]);

  useEffect(() => {
    if (!audioUrl) {
      return;
    }
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handlePlay = () => {
      if (!steps.length) {
        return;
      }
      if (lastStepIndexRef.current === -1) {
        lastStepIndexRef.current = 0;
        onAudioStep?.(steps[0].id);
      }
    };

    const handleTimeUpdate = () => {
      if (!steps.length || !Number.isFinite(audio.duration) || audio.duration <= 0) {
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
      if (steps.length) {
        lastStepIndexRef.current = steps.length - 1;
        onAudioStep?.(steps[steps.length - 1].id);
      }
      onAudioComplete?.();
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    let readyHandler: (() => void) | null = null;
    const attemptPlay = () => {
      if (!audioEnabled) {
        return;
      }
      audio
        .play()
        .catch(() => {
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
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      if (readyHandler) {
        audio.removeEventListener("canplaythrough", readyHandler);
        audio.removeEventListener("loadeddata", readyHandler);
      }
    };
  }, [audioEnabled, audioUrl, steps, onAudioStep, onAudioComplete, onAudioAutoplayFailure]);

  return (
    <div className="mt-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Data Story Timeline</h4>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      {audioUrl ? (
        <div className="mb-4">
          <audio ref={audioRef} controls className="w-full" preload="auto">
            <source src={audioUrl} type={audioContentType ?? "audio/mpeg"} />
            Your browser does not support the audio element.
          </audio>
        </div>
      ) : null}
      <ol className="space-y-4 border-l border-gray-200 pl-4">
        {steps.map((step, index) => {
          const isActive = step.id === activeStepId;
          return (
            <li key={step.id} className="relative">
              <span
                className={`absolute -left-2 top-1.5 flex h-3 w-3 -translate-x-1/2 rounded-full ${
                  isActive ? "bg-blue-600" : "bg-gray-300"
                }`}
              />
              <div className="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Step {index + 1}</p>
                    <h5 className="text-sm font-semibold text-gray-900">{step.title}</h5>
                  </div>
                  <button
                    type="button"
                    onClick={() => onReview(step.id)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                  >
                    Review
                  </button>
                </div>
                <div className="prose prose-sm mt-2 text-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdownTables(step.markdown)}</ReactMarkdown>
                </div>
                {step.kpis?.length ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {step.kpis.map((kpi) => (
                      <div
                        key={`${step.id}-${kpi.label}`}
                        className="rounded border border-gray-100 bg-gray-50 px-3 py-2"
                      >
                        <p className="text-xs text-gray-500">{kpi.label}</p>
                        <p className="text-sm font-semibold text-gray-800">{kpi.value}</p>
                      </div>
                    ))}
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
