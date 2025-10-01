# AG-UI Protocol Migration

## Summary of Completed Work
- Replaced the CopilotKit runtime with an AG-UI compliant FastAPI endpoint at `/ag-ui/run`, streaming `Run*`, `TextMessage*`, and `Custom` events via `ag_ui.encoder.EventEncoder`.
- Kept the Pydantic AI agent; responses are partitioned into markdown chunks and highlight directives that emit `chart.highlight` custom events.
- Added an AG-UI client shell for the Next.js app (`components/ag-ui/AgUiProvider.tsx`) that instantiates `HttpAgent`, manages thread/run state, subscribes to event streams, and dispatches highlights through a shared helper.
- Implemented a new sidebar (`components/ag-ui/AgUiSidebar.tsx`) that renders the transcript, shows streaming state, and publishes user prompts.
- Extracted chart highlighting logic into `lib/chart-highlighting.ts` so both markdown directives and AG-UI events reuse the same helper.
- Updated the root layout and page entry (`app/layout.tsx`, `app/page.tsx`) to use the AG-UI provider, remove CopilotKit readables/actions, and stabilise hydration.
- Refreshed dependencies (`package.json`, `backend/requirements.txt`) and project docs (`README.md`, `AGENTS.MD`) to describe the new protocol.

## Folder & File Changes
```
components/
  ag-ui/
    AgUiProvider.tsx      # AG-UI context + HttpAgent lifecycle
    AgUiSidebar.tsx       # Chat UI powered by AG-UI events
  AssistantMessage.tsx    # Markdown renderer with streaming indicator
  Dashboard.tsx           # Metrics view (no CopilotKit hooks)
lib/
  chart-highlighting.ts   # Shared highlight utilities for AG-UI custom events
app/
  layout.tsx              # Wraps tree with <AgUiProvider>
  page.tsx                # Uses AgUiSidebar and removes CopilotKit readables
backend/
  main.py                 # `/ag-ui/run` SSE endpoint + Tavily action
  requirements.txt        # Adds ag-ui-protocol, removes CopilotKit
```

## Updated Architecture Notes
### Frontend
- `AgUiProvider` owns the single `HttpAgent` instance, tracks messages/error state, and applies highlights when `chart.highlight` events arrive.
- `AgUiSidebar` consumes the provider, renders user/assistant bubbles, and posts prompts while the provider orchestrates streaming state.
- `AssistantMessage` now only handles markdown + spinner; highlight manipulation occurs via dedicated helper responding to custom events.
- Legacy CopilotKit constructs (`CopilotSidebar`, `useCopilotReadable`, `useCopilotAction`) were removed. Assistant instructions now live in `backend/prompts/analysis_agent_system_prompt.md`, and the provider relies on the backend to supply the system message over the AG-UI stream.

### Backend
- `/ag-ui/run` accepts AG-UI `RunAgentInput` payloads and streams SSE; `/copilotkit` now returns HTTP 410 for compatibility.
- Responses are split into message start/content/end events; highlight directives extracted with a regex drive `CustomEvent(name="chart.highlight")` notifications.
- `/ag-ui/action/searchInternet` stays as a REST action returning structured Tavily results; integrating it as a streaming tool call remains future work.

## Outstanding Follow-Ups
- AG-UI tool calls (e.g., Tavily search renders) are not yet surfaced in the sidebar; future iterations could emit custom events or adopt tool call events.
- Data story feature is still planned; current implementation only handles highlight directives. Additional AG-UI custom events will be required when the timeline work lands.
- Frontend/backend automated tests for the new event pipeline have not been added yet.

Use this document as the current snapshot of the migration; update it alongside any new AG-UI features.
