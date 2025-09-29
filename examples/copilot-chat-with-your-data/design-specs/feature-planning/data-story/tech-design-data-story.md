# Data Story Technical Design

## Overview
Introduce a guided "data story" experience that activates from the Copilot chat when broad performance questions are detected. The story renders a vertical timeline inside the chat, progressing from overview to detailed insights to summary, while synchronously highlighting dashboard charts and enabling highlight replays.

## Goals
- Detect user intents that warrant a data story suggestion.
- Surface an opt-in "Run Data Story" call-to-action (CTA) within the chat.
- Generate and stream structured story steps (overview, significant changes, summary) with chart mappings.
- Highlight dashboard cards in sync with timeline steps and allow replay via review buttons.
- Keep all interactions inside the existing CopilotKit session without duplicating conversation threads.

## Non-Goals
- Real-time ingestion of external data sources or warehouse connectivity.
- Persisting story history after the current chat session ends.
- Supporting multiple simultaneous users per chat session or cross-session collaboration.
- Replacing Azure OpenAI with alternate model providers.

## End-to-End Flow
1. User submits a broad performance question (e.g., "How are we doing this month?") in the `CopilotSidebar`.
2. Backend intent detector classifies the normalized utterance; if confidence ≥ 0.7, it emits a `dataStorySuggestion` meta event with intent context (timeframe hints, focus areas).
3. Frontend listens for meta events, renders a suggestion pill beneath the latest assistant message, and stores the recommendation in `useDataStoryState`.
4. User clicks "Run Data Story"; frontend invokes the `generateDataStory` action with the intent context and transitions UI state to `loading`.
5. Backend orchestrator retrieves the dashboard dataset, generates `StoryStep` entries (overview → change → summary), and streams them back via Server-Sent Events (SSE). JSON fallback returns an ordered array when SSE is unavailable.
6. Frontend `DataStoryTimeline` component renders each step as it arrives, calls shared highlight helpers to pulse relevant charts, and automatically scrolls to the newest step.
7. Each timeline block includes a "Review" button that triggers `replayHighlight(stepId)` to reapply stored highlight specs without recomputing analytics.
8. When the story completes, status transitions to `completed`; queued CTA recommendations (if any) may surface next.

## Frontend Design
- **State Management (`hooks/useDataStory.ts`)**
  - Maintain CTA queue, active story status (`idle` | `suggested` | `loading` | `playing` | `completed` | `error`), received steps, and highlight cache.
  - Provide actions: `enqueueSuggestion`, `dismissSuggestion`, `startStory`, `handleIncomingStep`, `completeStory`, `replayHighlight`.
  - Scope state by Copilot `threadId` to avoid cross-thread bleed.
- **Copilot Integration (`app/page.tsx`)**
  - Extend `CopilotSidebar` props with `onMetaEvent` callback to push `dataStorySuggestion` into the hook.
  - Pass `DataStorySuggestion` and `DataStoryTimeline` subcomponents into assistant responses through a custom renderer.
  - Continue exposing the live clock readable required by the project guidance.
- **Suggestion UI (`components/generative-ui/DataStorySuggestion.tsx`)**
  - Render CTA pill with summary text, `Run Data Story` button, and optional `Dismiss` link.
  - Disable the button while a story is loading.
- **Timeline UI (`components/generative-ui/DataStoryTimeline.tsx`)**
  - Vertical layout with progress indicator, step timestamps, markdown rendering for insight text, KPI badges, and a `Review` button.
  - Animate new steps with fade/slide transitions, respect reduced-motion preferences, and auto-scroll into view.
- **Highlight Helpers (`lib/chart-highlighting.ts`)**
  - Extract highlight logic from `components/AssistantMessage.tsx` into shared utilities: `applyHighlights(chartIds, highlightSpec)` and `clearHighlight(element)`.
  - Ensure both markdown directives and timeline steps reuse the same behavior to avoid divergence.
- **Dashboard Metadata (`components/Dashboard.tsx`)**
  - Keep `data-chart-id` attributes stable for all cards.
  - Export a `chartRegistry` map (chartId → DOM selector/title) so highlight helpers can resolve nodes without hard-coding selectors in multiple places.
- **Copilot Message Rendering (`components/AssistantMessage.tsx`)**
  - Replace inline highlight management with calls to `applyHighlights`/`clearExpiredHighlights`.
  - Allow subcomponents (suggestion/timeline) to mount below the assistant bubble via existing `subComponent` prop.

## Backend Design
- **Intent Detection (`backend/intent_detection.py`)**
  - Implement `DataStoryIntentDetector` using the Azure OpenAI deployment with a lightweight classification prompt.
  - Cache results per `(threadId, messageId)` to avoid redundant model calls on retries.
  - Return `{ intent: "data_story" | "none", confidence: float, timeframe?: {start, end}, focusAreas?: string[] }`.
- **Main Runtime Integration (`backend/main.py`)**
  - Before `_run_analysis`, call the detector; if `data_story` intent with sufficient confidence and no active story for the thread, append a `dataStorySuggestion` meta event to the GraphQL response.
  - Register new action route `/copilotkit/action/generateDataStory` that accepts `GenerateDataStoryRequest` payload and streams `StoryStep` events via `StreamingResponse` (SSE). Provide JSON array fallback when client lacks SSE support.
  - Ensure meta events remain optional so legacy clients ignoring unknown types still function.
- **Data Story Generator (`backend/data_story_generator.py`)**
  - Pure-Python analytics over `dashboard_data.get_dashboard_context()` to produce deterministic story content: latest month overview, significant month-over-month deltas, top positive/negative contributors, and summary with call-to-action.
  - Each step includes `chartIds`, KPI stats, highlight mode/duration, and optional follow-up prompt text.
- **Data Contracts (`backend/schemas.py` or updated `copilotkit_interfaces.py`)**
  - Define Pydantic models: `DataStoryMetaEvent`, `GenerateDataStoryRequest`, `StoryStep`, `HighlightSpec`, `DataStoryStreamChunk`.
  - Use these models for request validation and response serialization.

## Data Contracts (Frontend ↔ Backend)
- **Meta Event**
  ```json
  {
    "type": "dataStorySuggestion",
    "payload": {
      "intentId": "uuid",
      "confidence": 0.82,
      "summary": "I found a monthly performance story you can preview.",
      "timeframe": { "start": "2022-09-01", "end": "2022-12-31" },
      "focusAreas": ["sales", "profit"]
    }
  }
  ```
- **Generate Data Story Request**
  ```json
  {
    "intentId": "uuid",
    "timeframe": { "start": "2022-09-01", "end": "2022-12-31" },
    "focusAreas": ["sales"]
  }
  ```
- **Story Step**
  ```json
  {
    "id": "step-overview",
    "stepType": "overview",
    "title": "Overall performance remains strong",
    "markdown": "Revenue grew 12% month-over-month...",
    "chartIds": ["sales-overview"],
    "highlight": { "mode": "pulse", "durationMs": 6000 },
    "kpis": [{ "label": "Revenue", "value": "$6.8k", "trend": "up" }],
    "reviewPrompt": "Show sales overview again"
  }
  ```
- **SSE Stream Chunk**
  - `event: story-step` / `data: <StoryStep JSON>`
  - Terminal chunk `event: story-complete` with optional summary payload.

## State Management & Sync
- Track active story per Copilot `threadId` to support subsequent messages without losing context.
- Remove CTA once user accepts or dismisses it; queue additional suggestions while a story runs, but surface them only after completion.
- `replayHighlight` reuses cached highlight specs and cancels outstanding timers before reapplying to prevent overlap with new assistant messages.

## Security & Privacy
- No new secrets or external APIs introduced; analytics run on the existing static dataset.
- Validate all action payloads via Pydantic to guard against malformed requests.
- Adhere to existing CORS policy and only respond to configured origins.
- Ensure SSE endpoints do not leak conversation transcripts beyond the current thread.

## Performance Considerations
- Intent detection shares the Azure deployment; cache classifications to minimize incremental cost.
- Data story generation is deterministic and CPU-light on the static dataset (<10 ms); abstract logic to allow plugging in real analytics services later.
- SSE provides responsive UX; implement timeout fallback to buffered JSON when intermediaries strip events.
- Debounce highlight commands in the frontend helper to avoid rapid flicker when multiple steps reference the same chart.

## Testing Strategy
- **Frontend**
  - Unit tests for `useDataStory` to cover state transitions and action dispatches.
  - Component tests for `DataStoryTimeline` (step rendering, review button behavior, reduced-motion compliance).
  - Integration/Playwright scenario: trigger CTA, accept, verify timeline rendering, highlight activation, review replay.
- **Backend**
  - Unit tests for `DataStoryIntentDetector` prompt formatting/parsing (mock Azure client).
  - Tests for `DataStoryGenerator` ensuring deterministic output given fixed dataset and timeframe.
  - API tests for `/copilotkit/action/generateDataStory` covering SSE and non-streaming responses, error handling for invalid payloads, and idempotent replay by `intentId`.
  - Regression tests confirming standard chat responses remain unchanged when intent confidence is below threshold.

## Risks & Mitigations
- **False-positive CTAs**: Start with conservative confidence threshold, provide quick dismiss option, log confidence metrics for tuning.
- **Highlight conflicts**: Centralize highlight logic in shared helper, ensure cleanup runs when new assistant messages arrive.
- **Accessibility concerns**: Ensure timeline and review buttons have keyboard support and ARIA labels; respect reduced-motion setting in animations.

## Open Questions
- Should users be allowed to edit timeframe/focus before launching the story?
- Do we track CTA adoption metrics for future iteration?
- Should repeated "Run Data Story" offers be deduplicated within a single session?

## Implementation Steps
1. Scaffold `intent_detection.py` and `data_story_generator.py` with deterministic analytics and unit tests.
2. Update `backend/main.py` to emit meta events, register `generateDataStory`, and wire SSE streaming.
3. Extract highlight helpers, build `useDataStory` hook, and integrate suggestion/timeline components on the frontend.
4. Implement UI polish (animations, accessibility touches) and run automated/frontend-backend tests.
5. Manual smoke test: trigger CTA, run story, verify timeline progression and highlight replay.
