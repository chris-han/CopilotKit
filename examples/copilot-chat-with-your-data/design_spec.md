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
- **Frontend**: Next.js 15 (App Router) + React 19 client components.
- **Backend**: FastAPI application exposing CopilotKit remote runtime endpoints.
- **AI Services**: Azure OpenAI (model deployment) and Tavily API (optional external search).
- **Data Layer**: Static dataset representing dashboard metrics served locally.
- **Communication**: Browser interacts with FastAPI via HTTPS (REST + GraphQL-like payload) and receives streamed responses via CopilotKit provider.

## 3. Frontend Design
### 3.1 Structure
- `app/layout.tsx`: Wraps the app with `CopilotKit` provider and global styles.
- `app/page.tsx`: Main dashboard page; lazy-loads Copilot UI and hosts charts + metrics.
- `components/`: Shared UI components (header, footer, dashboard).
- `components/generative-ui/`: Copilot-specific UI helpers (e.g., search results renderer).
- `data/dashboard-data.ts`: Static JSON-like dataset containing revenue, churn, retention, etc.

### 3.2 Key Concepts
- **Copilot context**: `CopilotKit` provider configured with runtime URL (`NEXT_PUBLIC_COPILOT_RUNTIME_URL`).
- **Readable data**: `useCopilotReadable` exposes dashboard metrics to Copilot.
- **Copilot actions**: `useCopilotAction` to register render-only UI updates for runtime-triggered actions.
- **Sidebar**: `CopilotSidebar` from `@copilotkit/react-ui`, dynamically imported for bundle splitting.
- **Custom messages**: Component to render assistant responses with tailored styling.

### 3.3 Styling & UI
- Use Tailwind CSS (or CSS Modules) per existing example.
- Tremor/Recharts for charts (ensure dependencies listed).
- Responsive layout accommodating Copilot sidebar width adjustments.

## 4. Backend Design
### 4.1 FastAPI Application (`backend/main.py`)
- Initialize FastAPI app with title/version metadata.
- Load environment variables using `python-dotenv` (`.env`).
- Validate required Azure OpenAI settings at startup.
- **CORS**: Configure CORSMiddleware with normalized `FRONTEND_ORIGINS` allow-list.
- **Middleware**: Custom handler to respond to OPTIONS with proper CORS headers.
- **Endpoints**:
  - `GET /copilotkit`: Returns runtime metadata (actions, agents, SDK version).
  - `POST /copilotkit`: Main GraphQL-like endpoint handling Copilot conversation payloads.
  - `POST /copilotkit/action/searchInternet`: Tavily-backed action.
  - `POST /copilotkit/action/analyzeDashboard`: Runs AI analysis using dataset.
  - Trailing slash variants for compatibility.
  - `GET /health`: Health check for monitoring.

### 4.2 Azure OpenAI Integration
- Use `AsyncOpenAI` with custom base URL (`{endpoint}/openai/deployments/{deployment}`) and headers (`api-key`).
- PydanticAI `Agent` orchestrates prompts using the dataset context.
- API version default `2024-04-01-preview` adjustable via env var.

### 4.3 Tavily Integration
- Instantiate `TavilyClient` lazily per request to execute searches when action called.
- Return formatted markdown snippet summarizing search results.

### 4.4 Data Contracts (`backend/copilotkit_interfaces.py`)
- Dataclasses modeling CopilotKit GraphQL response types (message status, message output, overall response).
- `to_serializable` helper ensures dataclasses convert to JSON with `__typename` fields.

### 4.5 Prompt Handling
- Extract latest user prompt from incoming messages.
- Compose system + user prompts combining dataset JSON context.
- Handle errors from PydanticAI gracefully with HTTP 500, logging stack trace.

## 5. Dataset & Context
- `dashboard_data.py` (Python) and `data/dashboard-data.ts` (frontend) share same metrics structure (ensuring consistent context between UI and backend).
- Provide categories: revenue by month, churn rates, pipeline stages, customer segments, etc.
- Backend uses JSON serialization of dataset for prompt context.

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
- `next`, `react`, `react-dom`
- `@copilotkit/react-core`, `@copilotkit/react-ui`
- `tremor`, `recharts`, `clsx`, `tailwindcss`
- `eslint`, `typescript`, `postcss` for tooling

### Backend
- `fastapi`, `uvicorn`
- `aiohttp`/`httpx` (via OpenAI client)
- `python-dotenv`
- `tavily-python`
- `pydantic-ai`
- `openai`

### Tooling
- `bun` or `pnpm` for package management
- `ruff`/`black` optional for linting

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
2. Implement `app/layout.tsx` with fonts, global styles, and `CopilotKit` provider.
3. Build `app/page.tsx` combining header, dashboard, and lazy-loaded Copilot sidebar.
4. Implement `components/Header.tsx`, `Footer.tsx`, and shared layout wrappers.
5. Implement `components/Dashboard.tsx` with KPI cards, charts, and `useCopilotReadable` integration.
6. Implement `components/AssistantMessage.tsx` for assistant bubble rendering.
7. Create `components/generative-ui/SearchResults.tsx` to display action results.
8. Populate `data/dashboard-data.ts` with representative metrics.
9. Configure Tailwind styles and global CSS.
10. Validate accessibility (aria labels, semantic tags).

## Backend Implementation
1. Scaffold FastAPI project under `/backend` with `main.py`, `dashboard_data.py`, `copilotkit_interfaces.py`.
2. Load and validate environment variables (`dotenv`).
3. Configure CORS normalization helper and middleware.
4. Instantiate Azure OpenAI `AsyncOpenAI` client and PydanticAI agent.
5. Implement `_extract_prompt`, `_format_graphql_response`, and `_corsify` helpers.
6. Implement `/copilotkit` GET/POST endpoints handling GraphQL-like payload.
7. Implement Tavily action endpoint with guard for missing API key.
8. Implement analyze dashboard action reusing PydanticAI agent.
9. Add `/health` endpoint returning service status.
10. Ensure responses use dataclass serialization with `to_serializable`.
11. Add logging statements for key events and errors.

## Integration & Configuration
1. Align frontend `useCopilotReadable` data shape with backend `dashboard_data.py` JSON.
2. Set `NEXT_PUBLIC_COPILOT_RUNTIME_URL` default to `http://localhost:8004/copilotkit`.
3. Document runtime endpoints and actions for CopilotKit provider.
4. Provide instructions for running frontend (`bun run dev`) and backend (`uvicorn main:app --reload --port 8004`).

## Validation & QA
1. Start backend; confirm `/health` returns 200.
2. Start frontend; verify dashboard renders and Copilot sidebar connects.
3. Execute sample queries (e.g., "Summarize revenue trend") and confirm responses.
4. Test Tavily action by enabling API key and requesting web search.
5. Inspect browser DevTools for correct CORS headers and absence of errors.
6. Add unit tests for backend helpers and dataclass serialization.
7. Optionally add Playwright or Cypress tests for end-to-end chat flow.

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

