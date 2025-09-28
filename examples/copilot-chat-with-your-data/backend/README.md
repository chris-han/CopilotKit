# CopilotKit FastAPI Backend

This is a FastAPI backend with native CopilotKit integration that replaces the Next.js API route for containerized deployment.

## Features

- **CopilotKit Integration**: Native FastAPI support with streaming responses
- **Azure OpenAI**: Configured for Azure OpenAI deployments
- **Internet Search**: Tavily API integration for current information
- **Health Checks**: Container-ready with health endpoints
- **CORS Support**: Configured for frontend communication

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
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT`: Your deployment name
- `TAVILY_API_KEY`: Optional, for internet search functionality

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

- `GET /health` - Health check endpoint
- `POST /copilotkit` - CopilotKit runtime endpoint (used by frontend)
- `GET /docs` - FastAPI automatic documentation

## CopilotKit Actions

### searchInternet

Searches the internet for current information using Tavily API.

**Parameters:**
- `query` (string, required): Search query

**Returns:** Formatted search results with titles, content snippets, and source URLs.

## Configuration

The backend validates all required environment variables on startup and will fail fast if any are missing. This ensures container health checks work correctly in production deployments.