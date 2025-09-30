"use client";

import { ButtonHTMLAttributes } from "react";
import type { DataStorySuggestion, DataStoryStatus } from "../../hooks/useDataStory";

interface DataStorySuggestionProps {
  suggestion: DataStorySuggestion;
  status: DataStoryStatus;
  onRun: () => void;
  onDismiss: () => void;
}

export function DataStorySuggestion({ suggestion, status, onRun, onDismiss }: DataStorySuggestionProps) {
  const isLoading = status === "loading";

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-foreground">Data Story Available</h4>
          <p className="mt-1 text-sm text-muted-foreground">{suggestion.summary}</p>
          {suggestion.focusAreas?.length ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Focus areas: {suggestion.focusAreas.join(", ")}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          className="text-xs text-muted-foreground transition hover:text-foreground"
          onClick={onDismiss}
        >
          Dismiss
        </button>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <StoryButton disabled={isLoading} onClick={onRun}>
          {isLoading ? "Preparing..." : "Run Data Story"}
        </StoryButton>
        {suggestion.confidence != null && (
          <span className="text-xs text-muted-foreground">
            Confidence: {(suggestion.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
}

function StoryButton({ disabled, children, onClick }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {children}
    </button>
  );
}
