# AG-UI Protocol Migration Plan

## Objectives
- Replace CopilotKit communication with the AG-UI protocol so the dashboard's chat, timeline, and highlight interactions all run on standardized agent events.
- Keep the Pydantic AI FastAPI runtime but emit AG-UI compliant Server-Sent Events (SSE) using `ag-ui-protocol` Python SDK primitives.
- Rebuild the Next.js sidebar experience on top of `@ag-ui/client` (and supporting packages) so user inputs, streaming assistant messages, tool calls, and state deltas conform to AG-UI's frontend contract.

## Architecture Shifts
- **Frontend**
  - Introduce an `AgUiAgentProvider` that wraps the dashboard layout, instantiates an `HttpAgent` pointed at the FastAPI endpoint, and manages the shared thread/run lifecycle.
  - Build chat primitives (input composer, transcript, timeline surfaces) atop AG-UI event streams rather than CopilotKit message arrays.
  - Translate timeline/tool specific outputs (e.g., "Highlight chart card" directives, data story steps) into AG-UI custom events so UI modules subscribe via discriminated unions.
  - Use React context/hooks to share the current `threadId`, message history, and highlight controller across components.

- **Backend**
  - Replace GraphQL-style `/copilotkit` endpoint with `POST /ag-ui/run` that accepts `RunAgentInput` payloads (threadId, runId, messages, tools, context, forwardedProps) and streams encoded `BaseEvent` objects over SSE.
  - Leverage `ag_ui.encoder.EventEncoder` to serialize Pydantic events and reuse Pydantic AI agent outputs by mapping them to `TextMessage*` events, tool call events, and custom application events (for timeline data story).
  - Provide separate POST endpoints for agent-defined tools (e.g., `searchInternet`, `analyzeDashboard`, `generateDataStory`) that match AG-UI tool contract or embed as tool call responses within the SSE stream.
  - Maintain dataset parity and adopt AG-UI message shapes in the Pydantic agent's state.

- **Shared Contracts**
  - Define TypeScript + Python models for:
    - `DashboardContext` (unchanged data, but referenced in AG-UI context array)
    - `DataStorySuggestionEvent`, `DataStoryStepEvent` (custom event types conforming to AG-UI `CustomEvent` structure)
    - Tool descriptors (chart highlight, Tavily search) expressed as AG-UI `Tool` definitions passed from frontend in each run input.
  - Update highlight helpers to respond to AG-UI events rather than direct markdown directives.

## Incremental Workstream
1. **Backend foundation**
   - Add `ag-ui-protocol` dependency, implement SSE encoder pipeline, and expose `/ag-ui/run` endpoint bridging Pydantic AI responses to AG-UI events.
   - Provide compatibility shim (`/copilotkit` returning HTTP 410 + migration hint) until frontend switches over.

2. **Frontend agent shell**
   - Install `@ag-ui/client`, `@ag-ui/core`, optional `@ag-ui/react` (if available) plus `rxjs` dependencies.
   - Create `lib/ag-ui/agent.ts` handling `HttpAgent` lifecycle, `runAgent` invocation, and event subscription.
   - Replace `CopilotSidebar` usage with new `AgUiSidebar` implementing composer, transcript renderer, suggestion CTA, timeline mounting, and highlight dispatch.

3. **Feature parity**
   - Translate search + data story features into AG-UI tool calls/custom events, ensuring highlight logic and metrics readables remain accessible through AG-UI context/state events.
   - Update prompt instructions and dataset exposures so the assistant's behavior is unchanged post migration.

4. **Testing & docs**
   - Refresh design docs (`tech-design-data-story.md`) to reference AG-UI events.
   - Add backend unit tests around event encoding and SSE streaming, frontend tests for new hooks and components, and manual smoke instructions for AG-UI runs.

## Open Decisions
- Whether to keep separate endpoints for actions (`/action/*`) or model them as AG-UI tool executions embedded within the primary agent stream.
- How to persist thread state between reloads (local storage vs server-managed thread store) while keeping the UI stateless enough for ephemeral sessions.
- Strategy for gating AG-UI migration (feature flag vs hard switch).
