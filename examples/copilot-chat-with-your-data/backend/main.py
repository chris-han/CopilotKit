"""FastAPI CopilotKit runtime powered by PydanticAI and Tavily."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from tavily import Client as TavilyClient

from dashboard_data import DASHBOARD_CONTEXT

load_dotenv()


AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-04-01-preview")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY environment variable")
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("Missing AZURE_OPENAI_ENDPOINT environment variable")
if not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_DEPLOYMENT environment variable")

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,https://localhost:3000",
)
ALLOWED_ORIGINS = [origin.strip() for origin in FRONTEND_ORIGINS.split(",") if origin.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["http://localhost:3000"]

normalized_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
azure_client = AsyncOpenAI(
    base_url=f"{normalized_endpoint}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}",
    api_key=AZURE_OPENAI_API_KEY,
    default_query={"api-version": AZURE_OPENAI_API_VERSION},
    default_headers={"api-key": AZURE_OPENAI_API_KEY},
)

analysis_agent = Agent(
    model=OpenAIModel(openai_client=azure_client, model_name=AZURE_OPENAI_DEPLOYMENT),
    system_prompt=(
        "You are an efficient, professional data analyst. Use the dashboard dataset, respond in concise "
        "markdown, and highlight key metrics with tables when appropriate."
    ),
)


class CopilotMessage(BaseModel):
    id: str
    createdAt: datetime
    role: str
    content: str


app = FastAPI(title="CopilotKit FastAPI Runtime", version="1.0.0")
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
    "Starting FastAPI Copilot runtime (Azure endpoint=%s deployment=%s, Tavily configured=%s)",
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    bool(TAVILY_API_KEY),
)


def _extract_prompt(messages: List[Dict[str, Any]]) -> str:
    user_messages = []
    for message in messages:
        text_message = message.get("textMessage")
        if text_message and text_message.get("role") == "user":
            user_messages.append(text_message.get("content", ""))
    return user_messages[-1] if user_messages else ""


async def _run_analysis(question: str) -> str:
    prompt = (
        f"{question}\n\n"
        "You have access to the following dashboard context as JSON. Use it to answer.\n"
        f"```json\n{json.dumps(DASHBOARD_CONTEXT)}\n```"
    )
    try:
        result = await analysis_agent.run(prompt)
    except Exception as exc:  # pragma: no cover
        logger.exception("PydanticAI agent failed")
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc

    answer = getattr(result, "data", None)
    if answer is None:
        answer = getattr(result, "output_text", None)
    if answer is None:
        answer = str(result)
    return answer


def _format_graphql_response(
    thread_id: str,
    run_id: str,
    answer: str,
    parent_message_id: Optional[str],
) -> Dict[str, Any]:
    message_id = f"msg-{uuid4()}"
    created_at = datetime.now(timezone.utc).isoformat()

    return {
        "data": {
            "generateCopilotResponse": {
                "threadId": thread_id,
                "runId": run_id,
                "extensions": {
                    "openaiAssistantAPI": None,
                    "__typename": "CopilotResponseExtensions",
                },
                "status": {
                    "code": "success",
                    "__typename": "BaseResponseStatus",
                },
                "messages": [
                    {
                        "__typename": "TextMessageOutput",
                        "id": message_id,
                        "createdAt": created_at,
                        "status": {
                            "code": "success",
                            "__typename": "SuccessMessageStatus",
                        },
                        "content": [answer],
                        "role": "assistant",
                        "parentMessageId": parent_message_id,
                    }
                ],
                "metaEvents": [],
                "__typename": "CopilotResponse",
            }
        }
    }


def _format_info_response() -> Dict[str, Any]:
    return {
        "actions": _available_actions(),
        "agents": [],
        "sdkVersion": "custom-fastapi-runtime",
    }


def _available_actions() -> List[Dict[str, Any]]:
    return [
        {
            "name": "searchInternet",
            "description": "Searches the internet for current information using Tavily.",
            "parameters": [
                {
                    "name": "query",
                    "type": "string",
                    "description": "The query to search the internet for.",
                    "required": True,
                }
            ],
        },
        {
            "name": "analyzeDashboard",
            "description": "Analyzes the dashboard dataset with a PydanticAI agent.",
            "parameters": [
                {
                    "name": "question",
                    "type": "string",
                    "description": "Analysis question to run against the dashboard dataset.",
                    "required": True,
                }
            ],
        },
    ]


@app.get("/copilotkit")
async def copilot_info() -> Dict[str, Any]:
    return _format_info_response()


@app.post("/copilotkit")
async def copilot_runtime(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - guard against malformed JSON
        logger.exception("Failed to parse request body")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    logger.info("Received copilot runtime request: %s", payload.keys())
    operation = payload.get("operationName")

    if operation is None:
        logger.info("No operation supplied; returning runtime info")
        return JSONResponse(_format_info_response())

    if operation != "generateCopilotResponse":
        if operation == "availableActions":
            return JSONResponse({"data": {"availableActions": _available_actions()}})
        if operation == "availableAgents":
            return JSONResponse({"data": {"availableAgents": []}})
        logger.warning("Unsupported operation: %s", operation)
        raise HTTPException(status_code=400, detail="Unsupported operation")

    variables = payload.get("variables") or {}
    data = variables.get("data") or {}
    messages: List[Dict[str, Any]] = data.get("messages") or []

    thread_id = data.get("threadId") or str(uuid4())
    run_id = data.get("runId") or str(uuid4())
    parent_id = messages[-1].get("id") if messages else None

    question = _extract_prompt(messages)
    if not question:
        raise HTTPException(status_code=400, detail="Question not found in prompt")

    answer = await _run_analysis(question)

    response = _format_graphql_response(thread_id, run_id, answer, parent_id)
    return JSONResponse(response, media_type="application/graphql-response+json")


@app.post("/copilotkit/action/searchInternet")
async def action_search_internet(request: Request) -> Dict[str, Any]:
    if not TAVILY_API_KEY:
        raise HTTPException(status_code=503, detail="Tavily search is not configured")

    payload = await request.json()
    query = payload.get("arguments", {}).get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing query argument")

    logger.info("searchInternet invoked (query=%s)", query)

    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        results = tavily_client.search(query, max_results=5)
        formatted = []
        for result in results.get("results", []):
            title = result.get("title", "No title")
            content = (result.get("content", "No content") or "")[:200]
            url = result.get("url", "No URL")
            formatted.append(f"**{title}**\n{content}...\nSource: {url}")
        markdown = "\n\n".join(formatted) if formatted else f"No search results found for: {query}"
        return {"result": markdown}
    except Exception as exc:  # pragma: no cover
        logger.exception("searchInternet failed")
        raise HTTPException(status_code=500, detail=f"Search error: {exc}") from exc


@app.post("/copilotkit/action/analyzeDashboard")
async def action_analyze_dashboard(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    question = payload.get("arguments", {}).get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Missing question argument")

    logger.info("analyzeDashboard action invoked (question=%s)", question)
    answer = await _run_analysis(question)
    return {"result": answer}


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "copilotkit-fastapi-runtime",
        "azure_openai_configured": bool(AZURE_OPENAI_API_KEY),
        "tavily_configured": bool(TAVILY_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
