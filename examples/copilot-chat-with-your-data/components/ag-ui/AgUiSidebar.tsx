"use client";

import { useState } from "react";
import { AssistantMessage } from "../AssistantMessage";
import { DataStorySuggestion } from "../data-story/DataStorySuggestion";
import { DataStoryTimeline } from "../data-story/DataStoryTimeline";
import { useDataStory } from "../../hooks/useDataStory";
import { useAgUiAgent } from "./AgUiProvider";

export function AgUiSidebar() {
  const { messages, sendMessage, isRunning, error } = useAgUiAgent();
  const {
    state: dataStoryState,
    startStory,
    dismissSuggestion,
    replayHighlight,
    onAudioProgress,
    onAudioComplete,
    onAudioAutoplayFailure,
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

  return (
    <aside className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-xl border-l border-gray-200 flex flex-col">
      <header className="px-5 py-4 border-b border-gray-200">
        <div className="font-semibold text-gray-900 text-lg">Data Assistant</div>
        <p className="text-sm text-gray-500">
          Ask about sales trends, product performance, and key SaaS KPIs.
        </p>
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
              className="self-end max-w-xs ml-auto bg-blue-600 text-white text-sm rounded-lg px-3 py-2 shadow"
            >
              {message.content}
            </div>
          );
        })}
        {error && (
          <div className="text-red-600 text-sm">
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
          <div className="text-sm text-red-600">{dataStoryState.error}</div>
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
            onAudioStep={onAudioProgress}
            onAudioComplete={onAudioComplete}
            onAudioAutoplayFailure={onAudioAutoplayFailure}
          />
        )}
        {messages.length === 0 && !error && (
          <div className="text-sm text-gray-500">
            Try "How are we doing this month?" or "Highlight regional sales." The assistant will respond with insights and highlight relevant dashboard cards.
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={isRunning ? "Waiting for the assistant..." : "Ask about sales, trends, or metrics..."}
          className="w-full resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
          rows={3}
          disabled={isRunning}
          name="chat-prompt"
          id="chat-prompt"
        />
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            disabled={isRunning || !draft.trim()}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
          >
            {isRunning ? "Running" : "Send"}
          </button>
        </div>
      </form>
    </aside>
  );
}
