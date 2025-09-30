"use client";

import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { AssistantMessage } from "../AssistantMessage";
import { DataStorySuggestion } from "../data-story/DataStorySuggestion";
import { DataStoryTimeline } from "../data-story/DataStoryTimeline";
import { useDataStory } from "../../hooks/useDataStory";
import { useAgUiAgent } from "./AgUiProvider";
import clsx from "clsx";
import { X } from "lucide-react";

const HEADER_FALLBACK_PX = 88;

type AgUiSidebarProps = {
  open: boolean;
  docked: boolean;
  onClose: () => void;
};

export function AgUiSidebar({ open, docked, onClose }: AgUiSidebarProps) {
  const { messages, sendMessage, isRunning, error } = useAgUiAgent();
  const {
    state: dataStoryState,
    startStory,
    dismissSuggestion,
    replayHighlight,
    onAudioProgress,
    onAudioComplete,
    onAudioAutoplayFailure,
    onAudioReady,
  } = useDataStory();
  const [draft, setDraft] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }
    sendMessage(draft.trim());
    setDraft("");
  };

  const sidebarStyle = useMemo<CSSProperties>(
    () => ({
      top: `var(--app-header-height, ${HEADER_FALLBACK_PX}px)`,
      height: `calc(100dvh - var(--app-header-height, ${HEADER_FALLBACK_PX}px))`,
      right: open ? "0" : "-100vw",
    }),
    [open],
  );

  const containerClasses = clsx(
    "fixed z-40 flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl transition-all duration-300 ease-in-out",
    open ? "pointer-events-auto" : "pointer-events-none",
  );

  const presetSuggestions = useMemo(
    () => [
      {
        label: "How are we doing this month?",
        message: "How are we doing this month?",
      },
      {
        label: "Highlight regional sales",
        message: "Highlight regional sales for me.",
      },
      {
        label: "Show product performance insights",
        message: "Which products are driving the most profit right now?",
      },
    ],
    [],
  );

  return (
    <>
      {!docked && (
        <div
          className={clsx(
            "fixed inset-x-0 top-[var(--app-header-height,88px)] z-30 h-[calc(100dvh-var(--app-header-height,88px))] bg-background/60 backdrop-blur transition-opacity duration-300",
            open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
          )}
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={containerClasses}
        style={sidebarStyle}
        aria-hidden={!open}
      >
        <header className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="space-y-1">
            <div className="text-lg font-semibold text-foreground">Data Assistant</div>
            <p className="text-sm text-muted-foreground">
              Ask about sales trends, product performance, and key SaaS KPIs.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border text-muted-foreground transition hover:bg-muted"
            aria-label="Close data assistant"
          >
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.map((message) => {
            if (message.role === "assistant") {
              return (
                <AssistantMessage
                  key={message.id}
                  content={message.content}
                  isStreaming={Boolean(message.pending)}
                />
              );
            }

            return (
              <div
                key={message.id}
                className="ml-auto max-w-xs self-end rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground shadow"
              >
                {message.content}
              </div>
            );
          })}
          {error && (
            <div className="text-sm text-destructive">
              {error}
            </div>
          )}
          {dataStoryState.status === "suggested" && dataStoryState.suggestion && (
            <DataStorySuggestion
              suggestion={dataStoryState.suggestion}
              status={dataStoryState.status}
              onRun={() => startStory()}
              onDismiss={dismissSuggestion}
            />
          )}
          {dataStoryState.status === "error" && dataStoryState.error && (
            <div className="text-sm text-destructive">{dataStoryState.error}</div>
          )}
          {(dataStoryState.isAnalyzing || dataStoryState.status === "awaiting-audio") && (
            (() => {
              const showAnalyzing = Boolean(dataStoryState.isAnalyzing);
              const progressLabel = showAnalyzing ? "Analyzing dashboard" : "Generating data story";
              const progressDescription = showAnalyzing
                ? "Crunching metrics and charts"
                : "Synthesizing narration";
              const determinate = !showAnalyzing;
              const progress = determinate
                ? Math.max(0, Math.min(1, dataStoryState.audioGenerationProgress ?? 0))
                : 0;
              return (
                <div className="rounded-md border border-primary/20 bg-primary/5 p-4 text-sm text-primary shadow-sm">
                  <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-primary">
                    <span>{progressLabel}...</span>
                    <span>{progressDescription}</span>
                  </div>
                  <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-primary/20">
                    {determinate ? (
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-300"
                        style={{ width: `${Math.round(progress * 100)}%` }}
                      />
                    ) : (
                      <div className="h-full w-full animate-pulse rounded-full bg-primary" />
                    )}
                  </div>
                </div>
              );
            })()
          )}
          {dataStoryState.steps.length > 0 && (
            <DataStoryTimeline
              steps={dataStoryState.steps}
              activeStepId={dataStoryState.activeStepId}
              status={dataStoryState.status}
              onReview={replayHighlight}
              audioUrl={dataStoryState.audioUrl}
              audioEnabled={Boolean(dataStoryState.audioEnabled)}
              audioContentType={dataStoryState.audioContentType}
              audioSegments={dataStoryState.audioSegments}
              onAudioReady={onAudioReady}
              onAudioStep={onAudioProgress}
              onAudioComplete={onAudioComplete}
              onAudioAutoplayFailure={onAudioAutoplayFailure}
            />
          )}
          {messages.length === 0 && !error && (
            <div className="flex flex-wrap gap-2">
              {presetSuggestions.map((suggestion) => (
                <button
                  key={suggestion.message}
                  type="button"
                  onClick={() => sendMessage(suggestion.message)}
                  className="inline-flex cursor-pointer items-center justify-center rounded-full border border-border bg-muted px-4 py-2 text-sm font-medium text-foreground shadow-sm transition hover:bg-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  {suggestion.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="border-t border-border p-4">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={isRunning ? "Waiting for the assistant..." : "Ask about sales, trends, or metrics..."}
            className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-inner focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
            rows={3}
            disabled={isRunning}
            name="chat-prompt"
            id="chat-prompt"
          />
          <div className="mt-3 flex justify-end">
            <button
              type="submit"
              disabled={isRunning || !draft.trim()}
              className="inline-flex cursor-pointer items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
            >
              {isRunning ? "Running" : "Send"}
            </button>
          </div>
        </form>
      </aside>
    </>
  );
}
