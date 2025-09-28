"""FastAPI backend exposing Tavily search and PydanticAI-powered analytics actions."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from tavily import Client as TavilyClient

from dashboard_data import DASHBOARD_CONTEXT

# Load environment variables from .env if present
load_dotenv()


# Environment variables
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-04-01-preview")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,https://localhost:3000",
)
ALLOWED_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGINS.split(",") if origin.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["http://localhost:3000"]

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY environment variable")
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("Missing AZURE_OPENAI_ENDPOINT environment variable")
if not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_DEPLOYMENT environment variable")


# Initialize FastAPI app
app = FastAPI(title="CopilotKit Python Actions Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("copilotkit-backend")
logger.info(
    "Starting CopilotKit backend (Azure endpoint=%s deployment=%s, Tavily configured=%s)",
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    bool(TAVILY_API_KEY),
)


# Azure OpenAI-backed PydanticAI agent
normalized_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
azure_openai_client = AsyncOpenAI(
    base_url=f"{normalized_endpoint}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}",
    api_key=AZURE_OPENAI_API_KEY,
    default_query={"api-version": AZURE_OPENAI_API_VERSION},
    default_headers={"api-key": AZURE_OPENAI_API_KEY},
)

azure_model = OpenAIModel(
    model_name=AZURE_OPENAI_DEPLOYMENT,
    openai_client=azure_openai_client,
)
analysis_agent = Agent(
    model=azure_model,
    system_prompt=(
        "You are an efficient data analyst. Respond with concise, professional markdown. "
        "Use the structured dashboard data provided in context. Highlight key numbers in tables "
        "when it improves clarity."
    ),
)


# Pydantic request/response schemas
class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    results: str


class AnalysisRequest(BaseModel):
    question: str


class AnalysisResponse(BaseModel):
    answer: str
    model: str


def _format_tavily_results(results: dict[str, Any]) -> str:
    formatted_results: list[str] = []
    for result in results.get("results", []):
        title = result.get("title", "No title")
        content = (result.get("content", "No content") or "")[:200]
        url = result.get("url", "No URL")
        formatted_results.append(f"**{title}**\n{content}...\nSource: {url}")
    return "\n\n".join(formatted_results)


@app.post("/actions/search-internet", response_model=SearchResponse)
async def search_internet(request: SearchRequest) -> SearchResponse:
    """Perform a Tavily-powered internet search."""

    if not TAVILY_API_KEY:
        raise HTTPException(status_code=503, detail="Tavily search is not configured")

    logger.info("searchInternet invoked (query=%s)", request.query)
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        results = tavily_client.search(request.query, max_results=5)
        if not results.get("results"):
            return SearchResponse(results=f"No search results found for: {request.query}")
        return SearchResponse(results=_format_tavily_results(results))
    except Exception as exc:  # pragma: no cover - defensive logging for external service
        logger.exception("searchInternet encountered an error")
        raise HTTPException(status_code=500, detail=f"Search error: {exc}") from exc


@app.post("/actions/analyze-dashboard", response_model=AnalysisResponse)
async def analyze_dashboard(request: AnalysisRequest) -> AnalysisResponse:
    """Run a PydanticAI agent to analyse the dashboard dataset."""

    logger.info("analyzeDashboard invoked (question=%s)", request.question)
    context_payload = {
        "dashboard": DASHBOARD_CONTEXT,
    }

    try:
        result = await asyncio.to_thread(
            analysis_agent.run_sync,
            request.question,
            context=context_payload,
        )
    except Exception as exc:  # pragma: no cover - guard against LLM/SDK failures
        logger.exception("analyzeDashboard failed")
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc

    answer = getattr(result, "data", None)
    if answer is None:
        answer = str(result)

    return AnalysisResponse(answer=answer, model=AZURE_OPENAI_DEPLOYMENT)


@app.get("/health")
async def health_check():
    """Health check endpoint."""

    return {
        "status": "healthy",
        "service": "copilotkit-python-actions",
        "azure_openai_configured": bool(AZURE_OPENAI_API_KEY),
        "tavily_configured": bool(TAVILY_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
