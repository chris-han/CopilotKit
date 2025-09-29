# Copilot Chat with Your Data — Agent Guide

## Mission & Outcomes
- Deliver a dashboard-style Next.js web app where users ask natural-language questions about SaaS KPIs.
- Blend static KPI visualisations with an AI assistant that can highlight charts, run internal analyses, and optionally search the web.
- Keep the experience responsive, secure, and easy to extend for teams experimenting with CopilotKit integrations.

## System Architecture Snapshot
- **Frontend**: Next.js 15 App Router with React 19 client components in `app/` and `components/`, styled via Tailwind, local UI primitives, and Recharts wrappers.
- **CopilotKit Bridge**: `app/layout.tsx` wraps the tree with `CopilotKit` (`showDevConsole={false}`) pointing at `NEXT_PUBLIC_COPILOT_RUNTIME_URL` (default `http://localhost:8004/copilotkit`). All children share the same runtime session.
- **Chat Surface**: `app/page.tsx` dynamically loads the `CopilotSidebar`, manages layout offsets, registers a live clock readable, injects static assistant instructions from `lib/prompt.ts`, and sanitises assistant output through `components/AssistantMessage.tsx`.
- **Generative UI & Data Readables**: `components/Dashboard.tsx` computes KPI aggregates, exposes the full dataset and derived metrics through `useCopilotReadable`, and registers render-only Copilot actions so UI components reflect Tavily status.
- **Backend Runtime**: FastAPI app in `backend/main.py` hosts `/copilotkit`, handles CORS, validates configuration, and routes AI calls through Azure OpenAI using a PydanticAI agent. Optional Tavily search runs server-side.
- **Shared Contracts**: `backend/copilotkit_interfaces.py` and frontend helpers keep CopilotKit GraphQL envelopes consistent. Dataset parity lives in `data/dashboard-data.ts` and `backend/dashboard_data.py`.
- **External Services**: Azure OpenAI streams completions and powers the agent; Tavily Search augments answers when the runtime triggers `searchInternet`.

## Frontend Responsibilities
- Maintain layout and styling in Tailwind (`app/globals.css`) with highlight animations consumed by `CustomAssistantMessage`.
- Keep `CopilotSidebar` dynamically imported for bundle splitting, labelled "Data Assistant", and wired to custom markdown rendering + chart highlight directives.
- Ensure `useCopilotReadable` exposes:
  - Raw dashboard dataset and derived metrics (revenue, profit, conversion, retention, churn, etc.).
  - A live timestamp readable so the model references current time.
- Implement `useCopilotAction` registrations as render-only (`available: "disabled"`) to surface Tavily execution progress via `components/generative-ui/SearchResults.tsx` without client-side execution.
- Guard assistant responses in `components/AssistantMessage.tsx`: strip `Highlight chart card:` directives from visible markdown, toggle `chart-card-highlight` classes, and clean up highlights on new messages.
- Keep UI primitives in `components/ui/*.tsx` consistent with Recharts wrappers, tooltips, legends, and lucide-react status icons.

## Backend Responsibilities
- Load env vars via `python-dotenv`; require Azure OpenAI credentials (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, deployment name, API version). Optionally accept `TAVILY_API_KEY`.
- Normalise allowed origins from `FRONTEND_ORIGINS`, enforce them through `CORSMiddleware`, and short-circuit preflight `OPTIONS` requests.
- Instantiate `AsyncOpenAI` pointed at Azure; seed a `pydantic_ai.Agent` with the dashboard analyst system prompt.
- Provide `/copilotkit` POST handler that:
  - Accepts CopilotKit GraphQL-style payloads with conversation messages + readable context.
  - Streams responses via Azure OpenAI while brokering tool calls (`searchInternet`, `analyzeDashboard`).
  - Serialises responses using dataclasses defined in `backend/copilotkit_interfaces.py`.
- Implement runtime actions:
  - `searchInternet`: call Tavily when configured; return markdown summary + links, otherwise surface a graceful "unavailable" response.
  - `analyzeDashboard`: invoke the PydanticAI agent with shared dataset JSON and return insights markdown.
- Expose `/health` endpoint that reports service status and enabled integrations.

## Data & Prompt Alignment
- Keep the dashboard dataset synchronised between frontend and backend modules. Any schema changes must touch both `data/dashboard-data.ts` and `backend/dashboard_data.py`.
- Update `lib/prompt.ts` when adding new highlight directives, actions, or readable fields so the assistant has accurate instructions.
- Ensure JSON structures provided to the agent mirror what `useCopilotReadable` exposes; mismatches lead to hallucinations or schema errors.

## Configuration & Environment
- Document required environment variables in `.env.example` and surface defaults where safe.
- Frontend expects `process.env.NEXT_PUBLIC_COPILOT_RUNTIME_URL`; fallback is localhost port 8004.
- Backend logs startup state (runtime URL, Tavily availability) and should fail fast on missing Azure config.
- Secrets stay server-side; never ship API keys to the browser. Enforce HTTPS for production deployments.

## Local Development Workflow
1. Install frontend deps and run `bun run dev` (port 3000).
2. Create Python virtualenv in `/backend`, install dependencies, and start `uvicorn main:app --reload --port 8004`.
3. Verify `/health` returns 200 and that the Next.js app connects to the runtime (no console errors).
4. Test Copilot chat prompts, ensuring highlight directives animate cards and sidebar action status updates during Tavily calls.

## Quality & Testing Expectations
- Add frontend tests covering dashboard rendering, Copilot provider wiring, and highlight lifecycle.
- Add backend unit tests for dataclass serialisation, prompt extraction helpers, and action handlers.
- Smoke-test Copilot flows: ask for revenue trends, trigger Tavily search (with API key), and validate markdown rendering + highlight cleanup.
- Inspect browser DevTools for CORS headers, streaming completeness, and absence of runtime errors.

## Operability & Deployment
- Build production frontend with `bun run build`; containerise backend or deploy to FastAPI-friendly hosting.
- Maintain CI to lint, test, and build both halves.
- Provision infrastructure (e.g., Vercel + Azure App Service), set environment variables, enable HTTPS, logging, and monitoring.
- Plan future enhancements: SSE/WebSocket streaming, chat history persistence, real data sources, authentication, and role-based access.

## Extension Playbook
- To enrich insights, extend dashboard dataset files and refresh prompt instructions.
- Register new Copilot actions in FastAPI and expose render-only status components on the frontend.
- Update `CopilotSidebar` prompt + UI when adding new interaction patterns or visual directives.

Use this guide as the canonical reference for agents modifying or recreating the project end-to-end.
