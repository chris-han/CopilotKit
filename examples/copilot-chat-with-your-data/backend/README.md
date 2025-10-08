# AG-UI FastAPI Backend

This FastAPI service powers the AG-UI runtime used by the Next.js frontend. It replaces the legacy CopilotKit API route and centralises LLM orchestration, data story generation, and LIDA visualisation persistence.

## Features

- **AG-UI Protocol Runtime**: Streams events to the HttpAgent used in the frontend.
- **Azure OpenAI**: Handles analysis prompts plus optional text-to-speech narration.
- **Internet Search**: Tavily API integration for current information.
- **LIDA Persistence**: Optional Postgres-backed store for generated visualisations.
- **Health Checks & CORS**: Production-ready defaults for containerised deployments.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:

- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

Recommended/optional variables:

- `AZURE_OPENAI_TTS_DEPLOYMENT`, `AZURE_OPENAI_TTS_API_VERSION` – enable narrated data stories.
- `DATA_STORY_AUDIO_ENABLED` – toggle audio generation without changing code.
- `TAVILY_API_KEY` – configure server-side search augmentation.
- `FRONTEND_ORIGINS` – comma-separated list of allowed browser origins.
- `POSTGRES_*` – point at a Postgres instance to persist LIDA visualisations (otherwise falls back to in-memory storage).

### 3. Run the Server

```bash
# Development
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

The server will start on `http://localhost:8004`

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t copilotkit-backend .

# Run the container
docker run -p 8004:8004 --env-file .env copilotkit-backend
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8004:8004"
    env_file:
      - backend/.env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## API Endpoints

- `GET /health` – Health check endpoint.
- `POST /ag-ui/run` – Primary AG-UI streaming endpoint consumed by the frontend HttpAgent.
- `POST /ag-ui/database` – Direct database CRUD bridge for AG-UI `DirectDatabaseCRUD` messages.
- `GET /ag-ui/dashboard-data` – Streams the static dashboard context.
- `GET|POST|DELETE /lida/visualizations` – REST helpers for working with the LIDA store.
- `GET /docs` – FastAPI automatic documentation.

## Runtime Actions

### searchInternet

Searches the internet for current information using Tavily API.

**Parameters:**
- `query` (string, required): Search query

**Returns:** Formatted search results with titles, content snippets, and source URLs.

## Configuration

The backend validates critical Azure OpenAI configuration on startup and will fail fast if any required value is missing. Optional subsystems (Tavily, Postgres, audio narration) log informative warnings rather than crashing so local development continues to work.
