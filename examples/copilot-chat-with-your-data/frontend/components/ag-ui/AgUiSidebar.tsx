"use client";

import { useMemo, useState, useEffect } from "react";
import type { CSSProperties } from "react";
import { AssistantMessage } from "../AssistantMessage";
import { DataStorySuggestion } from "../data-story/DataStorySuggestion";
import { DataStoryTimeline } from "../data-story/DataStoryTimeline";
import { useDataStory } from "../../hooks/useDataStory";
import { useAgUiAgent } from "./AgUiProvider";
import { X, Save, RotateCcw } from "lucide-react";
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetTitle } from "../ui/sheet";
import { Button } from "../ui/button";
import { AddItemsCard, DashboardSettingsCard, DashboardPropertiesCard, ItemPropertiesCard } from "../dashboard/DashboardEditor";
import { useDashboardContext } from "../../contexts/DashboardContext";

type AgUiSidebarProps = {
  open: boolean;
  docked: boolean;
  onClose: () => void;
};

export function AgUiSidebar({ open, docked, onClose }: AgUiSidebarProps) {
  const { messages, sendAIMessage, isRunning, error } = useAgUiAgent();
  const dashboardContext = useDashboardContext();

  // Debug: Log activeSection and selectedItemId changes
  useEffect(() => {
    console.log('🎯 AgUiSidebar - activeSection changed:', dashboardContext.activeSection);
    console.log('🎯 AgUiSidebar - selectedItemId:', dashboardContext.selectedItemId);
  }, [dashboardContext.activeSection, dashboardContext.selectedItemId]);
  const {
    state: dataStoryState,
    startStory,
    dismissSuggestion,
    replayHighlight,
    onAudioProgress,
    onAudioComplete,
    onAudioAutoplayFailure,
    onAudioReady,
    onTalkingPointStart,
    onTalkingPointEnd,
  } = useDataStory();
  const [draft, setDraft] = useState("");



  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }
    sendAIMessage(draft.trim());
    setDraft("");
  };

  const sidebarDimensions = useMemo<CSSProperties>(
    () => ({ top: 0, height: "100dvh" }),
    [],
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

  const renderContent = (closeControl: React.ReactNode) => (
    <>
      <header className="flex flex-col gap-3 border-b border-border px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="text-lg font-semibold text-foreground">Data Assistant</div>
          </div>
          {closeControl}
        </div>
        {dashboardContext.dashboard && dashboardContext.mode === "edit" && dashboardContext.hasChanges && (
          <div className="flex items-center justify-between rounded-md border border-orange-200 bg-orange-50 px-4 py-3">
            <span className="text-sm text-orange-800">You have unsaved changes</span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  sendAIMessage("Reset all changes to the dashboard");
                  dashboardContext.onReset?.();
                }}
                disabled={isRunning || dashboardContext.saving}
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                Reset
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  sendAIMessage("Save all dashboard changes");
                  dashboardContext.onSave?.();
                }}
                disabled={isRunning || dashboardContext.saving}
              >
                <Save className="mr-2 h-4 w-4" />
                {dashboardContext.saving ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        )}
      </header>
      <div className="flex-1 overflow-y-auto space-y-4 px-5 py-4">
        {/* Context-aware content for dashboard editing */}
        {dashboardContext.dashboard && dashboardContext.mode === "edit" ? (
          <>
            {/* Dashboard Properties - shown when clicking dashboard title */}
            {dashboardContext.activeSection === "dashboard-title" && (
              <DashboardPropertiesCard
                dashboard={dashboardContext.dashboard}
                saving={dashboardContext.saving}
                onDashboardUpdate={(updates) => {
                  // Use specific context handlers for name and description changes
                  if (updates.name !== undefined && dashboardContext.onNameChange) {
                    dashboardContext.onNameChange(updates.name);
                  }
                  if (updates.description !== undefined && dashboardContext.onDescriptionChange) {
                    dashboardContext.onDescriptionChange(updates.description);
                  }
                }}
              />
            )}

            {/* Add Items and Dashboard Settings - shown when clicking Dashboard Preview or when item is selected */}
            {(dashboardContext.activeSection === "dashboard-preview" || dashboardContext.activeSection === "item-properties") && (
              <>
                <AddItemsCard
                  config={{
                    grid: dashboardContext.dashboard.layout_config?.grid || { cols: 4, rows: "auto" },
                    items: dashboardContext.dashboard.layout_config?.items || []
                  }}
                  onChange={(config) => {
                    if (dashboardContext.onDashboardChange && dashboardContext.dashboard) {
                      dashboardContext.onDashboardChange({
                        ...dashboardContext.dashboard,
                        layout_config: config
                      });
                    }
                  }}
                  onItemSelect={dashboardContext.onItemSelect}
                />
                <DashboardSettingsCard
                  config={{
                    grid: dashboardContext.dashboard.layout_config?.grid || { cols: 4, rows: "auto" },
                    items: dashboardContext.dashboard.layout_config?.items || []
                  }}
                  onChange={(config) => {
                    if (dashboardContext.onDashboardChange && dashboardContext.dashboard) {
                      dashboardContext.onDashboardChange({
                        ...dashboardContext.dashboard,
                        layout_config: config
                      });
                    }
                  }}
                />

                {/* Item Properties - shown when clicking dashboard item */}
                {dashboardContext.activeSection === "item-properties" && (
                  <ItemPropertiesCard
                    config={{
                      grid: dashboardContext.dashboard.layout_config?.grid || { cols: 4, rows: "auto" },
                      items: dashboardContext.dashboard.layout_config?.items || []
                    }}
                    onChange={(config) => {
                      if (dashboardContext.onDashboardChange && dashboardContext.dashboard) {
                        dashboardContext.onDashboardChange({
                          ...dashboardContext.dashboard,
                          layout_config: config
                        });
                      }
                    }}
                    selectedItemId={dashboardContext.selectedItemId}
                  />
                )}
              </>
            )}
          </>
        ) : (
          /* Default chat content */
          <>
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

            {/* Show storyline suggestions only for dynamic-dashboard */}
            {dashboardContext.isDynamicDashboard && dataStoryState.status === "suggested" && dataStoryState.suggestion && (
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
                activeTalkingPointId={dataStoryState.activeTalkingPointId}
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
                onTalkingPointStart={onTalkingPointStart}
                onTalkingPointEnd={onTalkingPointEnd}
              />
            )}
            {messages.length === 0 && !error && !dashboardContext.dashboard && (
              <div className="flex flex-wrap gap-2">
                {presetSuggestions.map((suggestion) => (
                  <button
                    key={suggestion.message}
                    type="button"
                    onClick={() => sendAIMessage(suggestion.message)}
                    className="inline-flex cursor-pointer items-center justify-center rounded-full border border-border bg-muted px-4 py-2 text-sm font-medium text-foreground shadow-sm transition hover:bg-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {suggestion.label}
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
        {/* Hide chat form in dashboard editing mode */}
        {(!dashboardContext.dashboard || dashboardContext.mode !== "edit") && (
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
        )}
    </>
  );

  if (docked) {
    if (!open) {
      return null;
    }

    return (
      <aside
        className="fixed right-0 z-60 flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl"
        style={{ ...sidebarDimensions, right: 0 }}
      >
        {renderContent(
          <button
            type="button"
            onClick={onClose}
            className="ml-auto inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border text-muted-foreground transition hover:bg-muted"
            aria-label="Close data assistant"
          >
            <X className="h-4 w-4" />
          </button>,
        )}
      </aside>
    );
  }

  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          onClose();
        }
      }}
    >
      <SheetContent
        side="right"
        className="w-full max-w-md border-l border-border bg-card p-0 shadow-xl"
        style={sidebarDimensions}
      >
        <div className="sr-only">
          <SheetTitle>Data Assistant</SheetTitle>
          <SheetDescription>Ask about sales trends, product performance, and key SaaS KPIs.</SheetDescription>
        </div>
        {renderContent(
          <SheetClose asChild>
            <button
              type="button"
              className="ml-auto inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-md border border-border text-muted-foreground transition hover:bg-muted"
              aria-label="Close data assistant"
            >
              <X className="h-4 w-4" />
            </button>
          </SheetClose>,
        )}
      </SheetContent>
    </Sheet>
  );
}
