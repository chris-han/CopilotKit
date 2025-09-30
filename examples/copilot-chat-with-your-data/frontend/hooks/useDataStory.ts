import { createContext, useContext } from "react";

import type { ChartFocusTarget } from "../lib/chart-highlighting";

export type DataStorySuggestion = {
  intentId: string;
  summary: string;
  confidence?: number;
  focusAreas?: string[];
};

export type DataStoryEvent = {
  name: string;
  value?: Record<string, unknown>;
};

export type DataStoryTalkingPoint = {
  id: string;
  markdown: string;
  chartIds?: string[];
  chartFocus?: ChartFocusTarget[];
};

export type DataStoryStep = {
  id: string;
  stepType: "overview" | "change" | "summary" | string;
  title: string;
  markdown: string;
  chartIds: string[];
  chartFocus?: ChartFocusTarget[];
  talkingPoints?: DataStoryTalkingPoint[];
  kpis?: Array<{ label: string; value: string; trend?: "up" | "down" | "neutral" }>;
  reviewPrompt?: string;
  agUiEvents?: DataStoryEvent[];
};

export type DataStoryAudioSegment = {
  stepId: string;
  talkingPointId?: string;
  url: string;
  contentType?: string;
};

export type DataStoryStatus =
  | "idle"
  | "suggested"
  | "loading"
  | "awaiting-audio"
  | "playing"
  | "completed"
  | "error";

export type DataStoryState = {
  status: DataStoryStatus;
  suggestion?: DataStorySuggestion;
  steps: DataStoryStep[];
  activeStepId?: string;
  error?: string | null;
  audioUrl?: string;
  audioEnabled?: boolean;
  audioContentType?: string;
  audioSegments?: DataStoryAudioSegment[];
  audioProgress?: number;
  audioGenerationProgress?: number;
  audioGenerationTotalSegments?: number;
  isAnalyzing?: boolean;
  hasTimeline?: boolean;
  activeTalkingPointId?: string;
};

export type DataStoryContextValue = {
  state: DataStoryState;
  dismissSuggestion: () => void;
  startStory: () => Promise<void> | void;
  replayHighlight: (stepId: string) => void;
  onAudioProgress: (stepId: string) => void;
  onAudioComplete: () => void;
  onAudioAutoplayFailure: () => void;
  onAudioReady: () => void;
  audioNarrationEnabled: boolean;
  onTalkingPointStart: (stepId: string, talkingPointId: string) => void;
  onTalkingPointEnd: (stepId: string, talkingPointId: string) => void;
};

export const DataStoryContext = createContext<DataStoryContextValue | null>(null);

export function useDataStory(): DataStoryContextValue {
  const ctx = useContext(DataStoryContext);
  if (!ctx) {
    throw new Error("useDataStory must be used within an AgUiProvider");
  }
  return ctx;
}
