# Design Specification: Copilot Chat with Your Data

This specification documents the full system design for the Copilot Chat with Your Data application so that an AI agent can recreate the project end-to-end. It covers user goals, architecture, module responsibilities, data contracts, dependencies, configuration, and operational concerns.

## 1. Product Overview
- **Purpose**: Provide a dashboard-style web application where users can ask natural-language questions about business metrics. Responses leverage a Copilot (LLM) runtime with optional internet search augmentation.
- **Core Outcomes**:
  - Display key performance indicators (KPIs) and charts for a fictional SaaS business.
  - Enable conversational analysis through a Copilot sidebar integrated with the dashboard.
  - Allow the AI to trigger actions such as dashboard analysis and web search.
- **Primary Users**: Data analysts, stakeholders wanting quick insights, and developers exploring CopilotKit integrations.

## 2. High-Level Architecture
- **Frontend**: Next.js 15 (App Router) + React 19 client components styled with Tailwind and custom Recharts wrappers.
- **Backend**: FastAPI application exposing CopilotKit remote runtime endpoints backed by a PydanticAI agent and Tavily integration.
- **AI Services**: Azure OpenAI (model deployment) and Tavily API (optional external search).
- **Data Layer**: Static dashboard dataset shared between the frontend (`data/dashboard-data.ts`) and backend (`backend/dashboard_data.py`).
- **Communication**: Browser interacts with FastAPI through CopilotKit's GraphQL-style POST payloads and receives streamed responses through the Copilot provider connection.

## 3. Frontend Design
### 3.1 Structure
- `app/layout.tsx`: Loads fonts, global styles, and wraps the tree with the `CopilotKit` provider (`showDevConsole={false}`) using `NEXT_PUBLIC_COPILOT_RUNTIME_URL` or a localhost default.
- `app/page.tsx`: Client entry point that manages sidebar layout offsets, registers a live `useCopilotReadable` clock, renders the `Dashboard`, and dynamically imports the `CopilotSidebar`.
- `components/Dashboard.tsx`: Calculates KPI metrics, exposes dataset context via `useCopilotReadable`, registers the render-only `searchInternet` action, and renders charts via reusable UI primitives.
- `components/AssistantMessage.tsx`: Custom Copilot message renderer that strips highlight directives, applies the `chart-card-highlight` CSS class, and renders markdown.
- `components/generative-ui/SearchResults.tsx`: Lightweight status component that mirrors Copilot action progress using `lucide-react` icons.
- `components/ui/*.tsx`: Card and chart wrappers built on top of Recharts with Tailwind-friendly defaults.
- `lib/prompt.ts`: Static assistant instructions that describe chart highlight directives and action usage.
- `data/dashboard-data.ts`: Shared dataset plus helper functions for total revenue, profit, conversion rate, etc.
- `app/globals.css`: Tailwind layer definitions and highlight animation styles consumed by `CustomAssistantMessage`.

### 3.2 Key Concepts
- **Copilot context**: `CopilotKit` provider configured with the runtime URL and dev console hidden to match production.
- **Readable data**: `useCopilotReadable` exposes the sales dataset, derived metrics, and a current time readable so the model always sees fresh numbers.
- **Chart directives**: The prompt asks the assistant to emit `Highlight chart card:` directives; `CustomAssistantMessage` interprets them and toggles CSS highlights.
- **Copilot actions**: `useCopilotAction` registers the `searchInternet` action as render-only (`available: "disabled"`) so the sidebar can surface Tavily progress without executing locally.
- **Sidebar**: `CopilotSidebar` from `@copilotkit/react-ui`, dynamically imported for bundle splitting and labelled “Data Assistant”.
- **Custom messages**: Component renders markdown with loading states and manages highlight lifecycle cleanup.

### 3.3 Styling & UI
- Tailwind CSS 4 utility classes with `clsx` + `tailwind-merge` helpers (`lib/utils.ts`) for composition.
- Recharts components wrapped in local UI primitives for consistent tooltips, legends, and colour palettes.
- `lucide-react` icons to communicate Copilot action state in `SearchResults`.
- Layout padding adjusts when the sidebar is open (`pr-[28rem]`) to keep the dashboard visible alongside Copilot.
- `chart-card-highlight` animation defined in `app/globals.css` for assistant-driven chart focus.

## 4. Backend Design
### 4.1 FastAPI Application (`backend/main.py`)
- Load environment variables with `python-dotenv`, validate Azure OpenAI configuration (API key, endpoint, deployment, API version), and compute allowed origins from `FRONTEND_ORIGINS`.
- Initialize FastAPI with title/version metadata, attach `CORSMiddleware`, and add an `OPTIONS` short-circuit middleware that mirrors the allow-list.
- Instantiate an `AsyncOpenAI` client pointed at the Azure deployment and a `pydantic_ai.Agent` seeded with a concise analyst system prompt.
- Log startup configuration (including whether Tavily is available) via the module logger.
- **Endpoints**:
  - `GET /copilotkit` + `/copilotkit/`: Return runtime info (`actions`, `agents`, `sdkVersion`).
  - `POST /copilotkit` + `/copilotkit/`: Handle Copilot GraphQL payloads, dispatching `generateCopilotResponse` to the analysis agent and short-circuiting `availableActions`/`availableAgents` queries.
  - `POST /copilotkit/action/searchInternet`: Tavily-backed action that returns markdown snippets or a 503 if the API key is missing.
  - `POST /copilotkit/action/analyzeDashboard` + trailing slash: Runs the PydanticAI analysis using the provided question argument.
  - `GET /health`: Lightweight health endpoint exposing which integrations are configured.

### 4.2 Azure OpenAI Integration
- Use `AsyncOpenAI` with custom base URL (`{endpoint}/openai/deployments/{deployment}`), `api-key` header, and query param `api-version` (default `2024-04-01-preview`).
- PydanticAI `Agent` executes the composed prompt, returning markdown strings consumed by CopilotKit.
- Azure deployment name doubles as the `model_name` passed to `OpenAIModel`.

### 4.3 Tavily Integration
- Instantiate `TavilyClient` on demand inside `searchInternet`, request up to five results, and format markdown with title/content/url per hit.
- Surface missing API key as HTTP 503 and wrap execution errors in HTTP 500 responses.

### 4.4 Data Contracts (`backend/copilotkit_interfaces.py`)
- Dataclasses mirror CopilotKit GraphQL response types (`CopilotResponse`, message statuses) and encode `__typename` metadata via dataclass field aliases.
- `to_serializable` recursively walks dataclasses, enums, lists, and dicts to generate JSON payloads consumed by the client.

### 4.5 Prompt Handling
- `_extract_prompt_details` iterates GraphQL message payloads to build the latest user message, capture system directives, and reconstruct transcript lines.
- `_run_analysis` merges system messages, transcript, the latest user question, and the JSON dashboard context before invoking the PydanticAI agent.
- Errors during analysis are logged and translated into HTTP 500s; successful responses are wrapped in CopilotKit's GraphQL envelope via `_format_graphql_response`.

## 5. Dataset & Context
- `backend/dashboard_data.py` exposes `DASHBOARD_CONTEXT` with `salesData`, `productData`, `categoryData`, `regionalData`, `demographicsData`, and aggregate metrics (`totalRevenue`, `profitMargin`, etc.).
- `data/dashboard-data.ts` mirrors the dataset and exports helper functions for totals, conversion rate, and margin calculations so the UI and Copilot stay synchronised.
- The backend serialises `DASHBOARD_CONTEXT` into the prompt, while the frontend passes the same structure through `useCopilotReadable`.

## 6. Configuration & Secrets
- `.env` variables required:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_DEPLOYMENT`
  - Optional: `AZURE_OPENAI_API_VERSION`, `TAVILY_API_KEY`, `FRONTEND_ORIGINS`
  - Frontend: `NEXT_PUBLIC_COPILOT_RUNTIME_URL`
- Ensure `.env` is not committed. Provide `.env.example` for guidance.

## 7. Dependencies
### Frontend
- `next@15.2.0-canary` with React/React DOM 19.
- `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime` for Copilot connectivity.
- `recharts` for charting plus local wrappers, `lucide-react` for icons, `clsx`/`tailwind-merge` utilities, and Tailwind CSS v4 (`@tailwindcss/postcss`).
- Shadcn-style UI helpers (`class-variance-authority`, Radix primitives) included for shared components.
- ESLint 9, TypeScript 5, and associated type packages.

### Backend
- `fastapi`, `uvicorn[standard]`, and `python-dotenv` for the web service.
- `copilotkit` (Python) GraphQL helpers and `pydantic-ai[openai]` for the agent runtime.
- `openai==1.58.1` configured for Azure endpoints.
- `tavily-python==0.5.0` for the `searchInternet` action.
- `python-multipart` to satisfy FastAPI's optional dependencies.

### Tooling
- Bun (default), npm, or pnpm for package management; `bun.lock` is checked in.
- Optional Python formatters/linting such as `ruff` or `black`.

## 8. Deployment Considerations
- Containerize backend with provided Dockerfile (python base image with uvicorn).
- Serve frontend via Vercel/Next hosting referencing runtime URL.
- Ensure HTTPS termination and environment variables available.

## 9. Observability
- Use Python logging for backend requests and errors.
- Optionally add frontend analytics for Copilot interactions.
- Health endpoint for uptime checks.

## 10. Security
- CORS restricted to normalized origins.
- Backend never exposes API keys to client; all secrets server-side.
- Validate payload structure and handle missing prompts with 400 responses.

## 11. Testing Strategy
- Unit tests for dataclass serialization.
- Integration tests mocking Azure OpenAI/Tavily to ensure endpoints respond.
- Frontend component tests for dashboard rendering and Copilot wrapper.

## 12. Future Enhancements
- Stream responses via Server-Sent Events (SSE) or WebSockets.
- Persist chat history server-side.
- Replace static dataset with real data source (database or API).
- Add authentication and role-based access.

---

# Implementation To-Do List

## Environment Setup
1. Initialize repository structure with `/app`, `/backend`, `/components`, `/data` directories.
2. Create `.nvmrc` or `.tool-versions` for Node/Bun version (optional but recommended).
3. Generate `package.json` and install frontend dependencies.
4. Set up Python virtual environment in `/backend` and install required packages.
5. Create `.env.example` documenting required variables.

## Frontend Implementation
1. Scaffold Next.js App Router project and configure TypeScript, ESLint, Tailwind.
2. Implement `app/layout.tsx` with fonts, global styles, hidden Copilot dev console, and runtime URL wiring.
3. Build `app/page.tsx` combining header/footer, dashboard, current-time readable, and lazy-loaded Copilot sidebar with layout offsets.
4. Implement shared UI primitives (`components/ui`, `Header`, `Footer`) with Tailwind utility classes.
5. Implement `components/Dashboard.tsx` with KPI cards, chart wrappers, `useCopilotReadable` dataset exposure, and render-only `searchInternet` action registration.
6. Populate `data/dashboard-data.ts` with representative metrics plus helper calculators.
7. Implement `components/AssistantMessage.tsx` to render markdown, show loading state, and interpret `Highlight chart card:` directives (tying into `app/globals.css`).
8. Create `components/generative-ui/SearchResults.tsx` to surface action execution status with lucide icons.
9. Configure Tailwind styles, highlight animations, and ensure responsive layout with sidebar offsets.
10. Validate accessibility (aria labels, semantic tags) across dashboard cards and sidebar controls.

## Backend Implementation
1. Scaffold FastAPI project under `/backend` with `main.py`, `dashboard_data.py`, `copilotkit_interfaces.py`.
2. Load and validate environment variables (`dotenv`) for Azure + Tavily config.
3. Configure CORS normalization helper and middleware (including OPTIONS short-circuit).
4. Instantiate Azure OpenAI `AsyncOpenAI` client and PydanticAI agent with dashboard-focused system prompt.
5. Implement `_extract_prompt_details`, `_run_analysis`, `_format_graphql_response`, and `_corsify` helpers.
6. Implement `/copilotkit` GET/POST endpoints handling GraphQL-like payloads and `availableActions`/`availableAgents` queries.
7. Implement Tavily action endpoint with guard for missing API key and markdown result formatting.
8. Implement analyze dashboard action reusing the PydanticAI agent and shared dataset.
9. Add `/health` endpoint returning service status and configured integrations.
10. Ensure responses use dataclass serialization with `to_serializable` and log runtime events/errors.

## Integration & Configuration
1. Align frontend `useCopilotReadable` data shape with backend `dashboard_data.py` JSON.
2. Set `NEXT_PUBLIC_COPILOT_RUNTIME_URL` default to `http://localhost:8004/copilotkit`.
3. Document runtime endpoints and actions for CopilotKit provider.
4. Provide instructions for running frontend (`bun run dev`) and backend (`uvicorn main:app --reload --port 8004`).

## Validation & QA
1. Start backend; confirm `/health` returns 200.
2. Start frontend; verify dashboard renders and Copilot sidebar connects.
3. Execute sample queries (e.g., "Summarize revenue trend") and confirm responses.
4. Test Tavily action by enabling API key and requesting web search while confirming the sidebar status component updates correctly.
5. Trigger highlight directives (e.g., "focus on regional sales") and ensure the appropriate cards animate and reset.
6. Inspect browser DevTools for correct CORS headers and absence of errors.
7. Add unit tests for backend helpers and dataclass serialization.
8. Optionally add Playwright or Cypress tests for end-to-end chat flow.

## Deployment Preparation
1. Build production Next.js app (`bun run build`).
2. Containerize backend using provided Dockerfile or create new Docker configuration.
3. Set up CI pipeline for lint/test/build.
4. Provision infrastructure (e.g., Azure App Service for backend, Vercel for frontend) with environment variables.
5. Configure HTTPS, logging, and monitoring in target environment.

## Documentation
1. Maintain `README.md` with setup instructions and environment requirements.
2. Keep `architecture.md` updated as architecture evolves.
3. Reference this design spec for implementation guidance.
