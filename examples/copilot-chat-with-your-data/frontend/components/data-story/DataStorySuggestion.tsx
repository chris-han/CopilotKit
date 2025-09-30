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
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-blue-900">Data Story Available</h4>
          <p className="text-sm text-blue-800 mt-1">{suggestion.summary}</p>
          {suggestion.focusAreas?.length ? (
            <p className="text-xs text-blue-700 mt-2">
              Focus areas: {suggestion.focusAreas.join(", ")}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          className="text-xs text-blue-700 hover:text-blue-900"
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
          <span className="text-xs text-blue-700">
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
      className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
    >
      {children}
    </button>
  );
}
