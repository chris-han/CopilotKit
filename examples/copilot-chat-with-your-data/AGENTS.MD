# AG-UI Data Assistant — Agent Guide

## Mission & Outcomes
- Deliver a dashboard-style Next.js web app where users ask natural-language questions about SaaS KPIs.
- Blend static KPI visualisations with an AI assistant that can highlight charts, run internal analyses, and optionally search the web.
- Keep the experience responsive, secure, and easy to extend for teams experimenting with AG-UI integrations.

## System Architecture Snapshot
- **Protocol Choice**: The project now speaks exclusively to the backend via the AG-UI protocol. Do not reintroduce CopilotKit SDK clients or endpoints; all chat or action traffic must flow through `/ag-ui` routes and the shared AG-UI provider.
- **Frontend**: Next.js 15 App Router with React 19 client components in `frontend/app/` and `frontend/components/`, styled via Tailwind, local UI primitives, and Recharts wrappers.
- **AG-UI Bridge**: `frontend/app/layout.tsx` wraps the tree with `AgUiProvider` pointing at `NEXT_PUBLIC_AG_UI_RUNTIME_URL` (default `http://localhost:8004/ag-ui/run`). All children share the same runtime session.
- **Chat Surface**: `frontend/app/page.tsx` renders the fixed `AgUiSidebar`, manages layout offsets, and streams assistant output through `frontend/components/AssistantMessage.tsx` while the backend injects instructions from `backend/prompts/analysis_agent_system_prompt.md`.
- **Highlight Integration**: `frontend/lib/chart-highlighting.ts` centralises chart highlighting so both AG-UI custom events and timeline components can toggle card focus.
- **Backend Runtime**: FastAPI app in `backend/main.py` hosts `/ag-ui/run`, handles CORS, validates configuration, and routes AI calls through Azure OpenAI using a PydanticAI agent. Optional Tavily search runs server-side.
- **Shared Contracts**: AG-UI protocol events (Run/Text/Custom) and highlight payloads stay in sync between frontend helpers and backend encoders. Dataset parity lives in `frontend/data/dashboard-data.ts` and `backend/dashboard_data.py`.
- **External Services**: Azure OpenAI streams completions and powers the agent; Tavily Search augments answers when the runtime triggers `searchInternet`.

## Frontend Responsibilities
- Maintain layout and styling in Tailwind (`frontend/app/globals.css`) with highlight animations consumed by `AssistantMessage` and AG-UI custom events.
- Keep `AgUiSidebar` fixed on wide viewports, labelled "Data Assistant", and wired to markdown rendering + highlight dispatch through `frontend/lib/chart-highlighting.ts`.
- Extend `AgUiProvider` so it handles new custom events, tool outputs, and thread state without breaking existing chat flows.
- Guard assistant responses in `frontend/components/AssistantMessage.tsx`: render markdown safely, surface streaming indicators, and rely on AG-UI custom events for highlight orchestration.
- Keep UI primitives in `frontend/components/ui/*.tsx` consistent with Recharts wrappers, tooltips, legends, and lucide-react status icons.

## Backend Responsibilities
- Load env vars via `python-dotenv`; require Azure OpenAI credentials (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, deployment name, API version). Optionally accept `TAVILY_API_KEY`.
- Normalise allowed origins from `FRONTEND_ORIGINS`, enforce them through `CORSMiddleware`, and short-circuit preflight `OPTIONS` requests.
- Instantiate `AsyncOpenAI` pointed at Azure; seed a `pydantic_ai.Agent` with the dashboard analyst system prompt.
- Provide `/ag-ui/run` POST handler that:
  - Accepts AG-UI `RunAgentInput` payloads with conversation messages, context, and forwarded props.
  - Streams responses as Server-Sent Events using `ag_ui.encoder.EventEncoder` (Run/Text/Custom events).
  - Emits `chart.highlight` custom events derived from model directives.
- Implement runtime actions exposed via REST endpoints (e.g., `/ag-ui/action/searchInternet`) or custom events; ensure they respect Tavily configuration and error handling.
- Expose `/health` endpoint that reports service status and enabled integrations.

## Data & Prompt Alignment
- Keep the dashboard dataset synchronised between frontend and backend modules. Any schema changes must touch both `data/dashboard-data.ts` and `backend/dashboard_data.py`.
- Update `backend/prompts/analysis_agent_system_prompt.md` when adding new highlight directives, custom events, or contextual hints so the assistant has accurate instructions.
- Ensure AG-UI events emitted by the backend map cleanly to frontend handlers; mismatches lead to silent UI failures.

## Configuration & Environment
- Document required environment variables in `.env.example` and surface defaults where safe.
- Frontend expects `process.env.NEXT_PUBLIC_AG_UI_RUNTIME_URL`; fallback is `http://localhost:8004/ag-ui/run`.
- Backend logs startup state (runtime URL, Tavily availability) and should fail fast on missing Azure config.
- Secrets stay server-side; never ship API keys to the browser. Enforce HTTPS for production deployments.

## Local Development Workflow
1. From `frontend/`, install dependencies and run `bun run dev` (port 3000).
2. Create Python virtualenv in `/backend`, install dependencies, and start `uvicorn main:app --reload --port 8004`.
3. Verify `/health` returns 200 and that the Next.js app connects to the runtime (no console errors).
4. Test AG-UI chat prompts, ensuring highlight custom events animate cards and streaming updates stay responsive.

## Quality & Testing Expectations
- Add frontend tests covering dashboard rendering, AG-UI provider wiring, and highlight lifecycle.
- Add backend unit tests for event encoding, prompt extraction helpers, and action handlers.
- Smoke-test AG-UI flows: ask for revenue trends, trigger Tavily search (with API key), and validate markdown rendering + highlight cleanup.
- Inspect browser DevTools for CORS headers, streaming completeness, and absence of runtime errors.

## Operability & Deployment
- Build production frontend with `bun run build`; containerise backend or deploy to FastAPI-friendly hosting.
- Maintain CI to lint, test, and build both halves.
- Provision infrastructure (e.g., Vercel + Azure App Service), set environment variables, enable HTTPS, logging, and monitoring.
- Plan future enhancements: SSE/WebSocket streaming, chat history persistence, real data sources, authentication, and role-based access.

## Extension Playbook
- To enrich insights, extend dashboard dataset files and refresh prompt instructions.
- Register new AG-UI custom events or REST actions in FastAPI and expose render-only status components on the frontend.
- Update `AgUiSidebar` prompt + UI when adding new interaction patterns or visual directives.

Use this guide as the canonical reference for agents modifying or recreating the project end-to-end.
