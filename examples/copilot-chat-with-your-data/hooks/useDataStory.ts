import { createContext, useContext } from "react";

export type DataStorySuggestion = {
  intentId: string;
  summary: string;
  confidence?: number;
  focusAreas?: string[];
};

export type DataStoryStep = {
  id: string;
  stepType: "overview" | "change" | "summary" | string;
  title: string;
  markdown: string;
  chartIds: string[];
  kpis?: Array<{ label: string; value: string; trend?: "up" | "down" | "neutral" }>;
  reviewPrompt?: string;
};

export type DataStoryStatus = "idle" | "suggested" | "loading" | "playing" | "completed" | "error";

export type DataStoryState = {
  status: DataStoryStatus;
  suggestion?: DataStorySuggestion;
  steps: DataStoryStep[];
  activeStepId?: string;
  error?: string | null;
  audioUrl?: string;
  audioEnabled?: boolean;
  audioContentType?: string;
};

export type DataStoryContextValue = {
  state: DataStoryState;
  dismissSuggestion: () => void;
  startStory: () => Promise<void> | void;
  replayHighlight: (stepId: string) => void;
  onAudioProgress: (stepId: string) => void;
  onAudioComplete: () => void;
  onAudioAutoplayFailure: () => void;
  audioNarrationEnabled: boolean;
};

export const DataStoryContext = createContext<DataStoryContextValue | null>(null);

export function useDataStory(): DataStoryContextValue {
  const ctx = useContext(DataStoryContext);
  if (!ctx) {
    throw new Error("useDataStory must be used within an AgUiProvider");
  }
  return ctx;
}
