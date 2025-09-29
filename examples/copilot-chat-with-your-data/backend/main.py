"""FastAPI AG-UI runtime powered by Pydantic AI and Tavily."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import Any, AsyncIterator, Dict, Iterable, List, Sequence, Tuple
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
import httpx
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from tavily import Client as TavilyClient
from urllib.parse import urlparse

from ag_ui.core import (
    CustomEvent,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder

from dashboard_data import DASHBOARD_CONTEXT
from data_story_generator import generate_data_story_steps
from intent_detection import detect_data_story_intent

load_dotenv()


AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-04-01-preview")
AZURE_OPENAI_TTS_DEPLOYMENT = os.getenv("AZURE_OPENAI_TTS_DEPLOYMENT") or "gpt-4o-mini-tts"
AZURE_OPENAI_TTS_API_VERSION = os.getenv("AZURE_OPENAI_TTS_API_VERSION", "2025-03-01-preview")
DATA_STORY_AUDIO_ENABLED = (os.getenv("DATA_STORY_AUDIO_ENABLED", "true").lower() not in {"false", "0", "no"})
DATA_STORY_AUDIO_INSTRUCTIONS = os.getenv(
    "DATA_STORY_AUDIO_INSTRUCTIONS",
    "You are a professional financial analyst. Speak confidently and when attention need, use a brief pause before proceeding with your points.",
)
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


def _normalize_origin(origin: str) -> str:
    """Normalize configured origins so minor formatting differences still match."""

    cleaned = origin.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        path = parsed.path.rstrip("/") if parsed.path not in {"", "/"} else ""
        normalized = f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
        return f"{normalized}{path}"
    return cleaned.rstrip("/")


def _build_allowed_origins(frontend_origins: str) -> List[str]:
    configured = {
        _normalize_origin(origin)
        for origin in frontend_origins.split(",")
        if origin.strip()
    }
    if not configured:
        configured = {"http://localhost:3000"}

    defaults = {
        "http://localhost:3000",
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000",
    }
    return sorted(configured.union(_normalize_origin(default) for default in defaults))


ALLOWED_ORIGINS = _build_allowed_origins(FRONTEND_ORIGINS)
azure_client = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)

analysis_agent = Agent(
    model=OpenAIModel(openai_client=azure_client, model_name=AZURE_OPENAI_DEPLOYMENT),
    system_prompt=(
        "You are an efficient, professional data analyst. Use the dashboard dataset, respond in concise "
        "markdown, and highlight key metrics with tables when appropriate."
    ),
)

encoder = EventEncoder()

DATA_STORY_INTENTS: Dict[str, Dict[str, Any]] = {}


app = FastAPI(title="CopilotKit FastAPI Runtime", version="2.0.0")
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
    "Starting AG-UI FastAPI runtime (Azure endpoint=%s deployment=%s, Tavily configured=%s)",
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    bool(TAVILY_API_KEY),
)
logger.info("Allowed frontend origins: %s", ALLOWED_ORIGINS)


HIGHLIGHT_LINE_REGEX = re.compile(r"^Highlight chart cards?:\s*(.+)$", re.MULTILINE)


@app.middleware("http")
async def handle_options(request: Request, call_next):
    if request.method == "OPTIONS":
        return _corsify(Response(status_code=200), request)
    response = await call_next(request)
    return _corsify(response, request)


def _corsify(response: Response, request: Request) -> Response:
    origin = request.headers.get("origin")
    normalized_origin = _normalize_origin(origin) if origin else None
    if origin and normalized_origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    response.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    response.headers.setdefault("Access-Control-Allow-Headers", "*")
    return response


def _extract_prompt_details(messages: Sequence[Any]) -> Tuple[str, List[str], List[Tuple[str, str]]]:
    """Return latest user message, system messages, and chat transcript."""

    latest_user = ""
    system_messages: List[str] = []
    transcript: List[Tuple[str, str]] = []

    for message in messages:
        role = getattr(message, "role", "") or ""
        content = getattr(message, "content", "")
        if not content:
            continue

        if role == "system":
            system_messages.append(content)
        else:
            transcript.append((role, content))
            if role == "user":
                latest_user = content

    return latest_user, system_messages, transcript


async def _run_analysis(
    latest_user: str,
    system_messages: Sequence[str],
    transcript: Sequence[Tuple[str, str]],
) -> str:
    prompt_sections: List[str] = []

    if system_messages:
        prompt_sections.append("\n\n".join(system_messages))

    if transcript:
        conversation_lines = []
        for role, content in transcript:
            role_label = {
                "user": "User",
                "assistant": "Assistant",
                "system": "System",
                "tool": "Tool",
            }.get(role, role.title() if role else "Message")
            conversation_lines.append(f"{role_label}: {content}")
        prompt_sections.append("Conversation so far:\n" + "\n".join(conversation_lines))

    prompt_sections.append(f"Latest user request:\n{latest_user}")

    prompt_sections.append(
        "You have access to the following dashboard context as JSON. Use it to answer.\n"
        f"```json\n{json.dumps(DASHBOARD_CONTEXT)}\n```"
    )

    prompt = "\n\n".join(part for part in prompt_sections if part.strip())
    result = await analysis_agent.run(prompt)

    answer = getattr(result, "data", None)
    if answer is None:
        answer = getattr(result, "output_text", None)
    if answer is None:
        answer = str(result)
    return answer


def _separate_highlight_directives(answer: str) -> Tuple[str, List[str]]:
    chart_ids: List[str] = []
    used_lines = set()

    for match in HIGHLIGHT_LINE_REGEX.finditer(answer):
        start, end = match.span()
        used_lines.update(range(start, end))
        raw_ids = match.group(1).strip()
        if raw_ids:
            for part in re.split(r"[;,\s]+", raw_ids):
                cleaned = part.strip().strip("`").rstrip(".,;:")
                if cleaned:
                    chart_ids.append(cleaned)

    lines = answer.splitlines()
    sanitized_lines: List[str] = []
    skip_block = False

    for line in lines:
        original_line = line
        stripped = line.strip()

        if HIGHLIGHT_LINE_REGEX.match(line):
            skip_block = True
            continue

        if skip_block:
            if not stripped:
                skip_block = False
                continue

            if " " not in stripped and stripped.lower() == stripped:
                cleaned = stripped.strip("`").rstrip(".,;:")
                if cleaned:
                    chart_ids.append(cleaned)
                continue

        sanitized_lines.append(original_line)

    unique_ids = list(dict.fromkeys(chart_ids))

    sanitized_answer = "\n".join(line for line in sanitized_lines if line.strip() or line == "").strip()
    return sanitized_answer, unique_ids


def _markdown_to_text(markdown: str) -> str:
    if not markdown:
        return ""
    text = re.sub(r"`+", "", markdown)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"[_*]", "", text)
    text = re.sub(r"[>#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _story_steps_to_audio_segments(steps: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    segments: List[Dict[str, str]] = []
    for index, step in enumerate(steps, start=1):
        step_id = step.get("id") or f"step-{index}"
        title = step.get("title") or f"Section {index}"
        body = _markdown_to_text(step.get("markdown", ""))
        if body:
            script = f"Section {index}. {title}. {body}"
        else:
            script = f"Section {index}. {title}."
        segments.append({"stepId": step_id, "script": script})
    return segments


def _chunk_text(text: str, max_len: int = 800) -> Iterable[str]:
    if not text:
        return []
    lines = text.splitlines()
    buffer: List[str] = []
    current_len = 0
    for line in lines:
        line_with_newline = line + "\n"
        if current_len + len(line_with_newline) > max_len and buffer:
            yield "".join(buffer).rstrip("\n")
            buffer = [line_with_newline]
            current_len = len(line_with_newline)
        else:
            buffer.append(line_with_newline)
            current_len += len(line_with_newline)
    if buffer:
        yield "".join(buffer).rstrip("\n")


async def _agent_event_stream(run_input: RunAgentInput) -> AsyncIterator[str]:
    thread_id = run_input.thread_id or f"thread-{uuid4()}"
    run_id = run_input.run_id or f"run-{uuid4()}"
    latest_user, system_messages, transcript = _extract_prompt_details(run_input.messages)

    if not latest_user:
        event = RunErrorEvent(
            type=EventType.RUN_ERROR,
            message="No user message provided",
            code="400",
        )
        yield encoder.encode(event)
        return

    intent_result = detect_data_story_intent(latest_user)

    started_event = RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id)
    yield encoder.encode(started_event)

    if intent_result:
        intent_id = str(uuid4())
        DATA_STORY_INTENTS[intent_id] = {
            "threadId": thread_id,
            "summary": intent_result.summary,
            "confidence": intent_result.confidence,
            "focusAreas": intent_result.focus_areas,
        }
        suggestion_event = CustomEvent(
            type=EventType.CUSTOM,
            name="dataStory.suggestion",
            value={
                "intentId": intent_id,
                "summary": intent_result.summary,
                "confidence": intent_result.confidence,
                "focusAreas": intent_result.focus_areas,
            },
        )
        yield encoder.encode(suggestion_event)

    message_id = f"msg-{uuid4()}"

    try:
        answer = await _run_analysis(latest_user, system_messages, transcript)
        sanitized_answer, chart_ids = _separate_highlight_directives(answer)

        start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
        )
        yield encoder.encode(start_event)

        for chunk in _chunk_text(sanitized_answer):
            content_event = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=chunk,
            )
            yield encoder.encode(content_event)

        end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id,
        )
        yield encoder.encode(end_event)

        for chart_id in chart_ids:
            custom_event = CustomEvent(
                type=EventType.CUSTOM,
                name="chart.highlight",
                value={"chartId": chart_id, "messageId": message_id},
            )
            yield encoder.encode(custom_event)

        finished_event = RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=thread_id,
            run_id=run_id,
        )
        yield encoder.encode(finished_event)
    except HTTPException as http_exc:
        error_event = RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=str(http_exc.detail),
            code=str(http_exc.status_code),
        )
        yield encoder.encode(error_event)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Analysis agent failed")
        error_event = RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=f"Analysis error: {exc}",
            code="500",
        )
        yield encoder.encode(error_event)


@app.post("/ag-ui/run")
async def ag_ui_run(request: Request) -> StreamingResponse:
    try:
        payload = await request.json()
    except Exception as exc:  # pragma: no cover - guard against malformed JSON
        logger.exception("Failed to parse request body")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    try:
        run_input = RunAgentInput.model_validate(payload)
    except Exception as exc:
        logger.exception("Invalid AG-UI payload")
        raise HTTPException(status_code=400, detail=f"Invalid AG-UI payload: {exc}") from exc

    async def event_iterator() -> AsyncIterator[str]:
        async for event in _agent_event_stream(run_input):
            yield event

    return StreamingResponse(event_iterator(), media_type="text/event-stream")


@app.post("/copilotkit")
async def deprecated_copilot_endpoint() -> JSONResponse:
    return JSONResponse(
        status_code=410,
        content={
            "error": "The CopilotKit runtime has been replaced by the AG-UI protocol endpoint at /ag-ui/run.",
        },
    )


@app.post("/copilotkit/")
async def deprecated_copilot_endpoint_trailing() -> JSONResponse:
    return await deprecated_copilot_endpoint()


@app.post("/ag-ui/action/searchInternet")
async def action_search_internet(request: Request) -> dict[str, Any]:
    if not TAVILY_API_KEY:
        raise HTTPException(status_code=503, detail="Tavily search is not configured")

    payload = await request.json()
    query = payload.get("query")
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
            formatted.append({
                "title": title,
                "summary": f"{content}...",
                "url": url,
            })
        return {"results": formatted}
    except Exception as exc:  # pragma: no cover
        logger.exception("searchInternet failed")
        raise HTTPException(status_code=500, detail=f"Search error: {exc}") from exc


@app.post("/ag-ui/action/generateDataStory")
async def action_generate_data_story(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    intent_id = payload.get("intentId")

    steps = generate_data_story_steps()
    info = DATA_STORY_INTENTS.get(intent_id or "")

    response: Dict[str, Any] = {
        "storyId": intent_id or f"story-{uuid4()}",
        "steps": steps,
    }

    if info:
        response["summary"] = info.get("summary")
        response["focusAreas"] = info.get("focusAreas")
        DATA_STORY_INTENTS.pop(intent_id or "", None)

    return response


@app.post("/ag-ui/action/generateDataStoryAudio")
async def action_generate_data_story_audio(request: Request) -> Dict[str, Any]:
    if not DATA_STORY_AUDIO_ENABLED:
        raise HTTPException(status_code=503, detail="Audio narration disabled")

    request_payload = await request.json()
    steps = request_payload.get("steps")
    if not isinstance(steps, list) or not steps:
        steps = generate_data_story_steps()

    script_segments = _story_steps_to_audio_segments(steps)
    if not script_segments:
        raise HTTPException(status_code=400, detail="Story steps are empty")

    tts_url = (
        f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_OPENAI_TTS_DEPLOYMENT}/audio/speech"
        f"?api-version={AZURE_OPENAI_TTS_API_VERSION}"
    )
    audio_segments: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            for segment in script_segments:
                step_id = segment.get("stepId")
                narration = segment.get("script") or ""

                tts_payload = {
                    "model": AZURE_OPENAI_TTS_DEPLOYMENT,
                    "voice": "alloy",
                    "response_format": "mp3",
                    "input": narration,
                    "instructions": DATA_STORY_AUDIO_INSTRUCTIONS,
                }

                try:
                    rest_response = await client.post(
                        tts_url,
                        headers={
                            "api-key": AZURE_OPENAI_API_KEY,
                            "Content-Type": "application/json",
                            "Accept": "audio/mpeg",
                        },
                        json=tts_payload,
                    )
                    rest_response.raise_for_status()
                except httpx.HTTPStatusError as exc:  # pragma: no cover
                    body_preview = exc.response.text[:200] if exc.response.text else ""
                    logger.warning(
                        "generateDataStoryAudio step %s HTTP %s: %s",
                        step_id,
                        exc.response.status_code,
                        body_preview,
                    )
                    if exc.response.status_code == 404:
                        return {"audio": None, "segments": [], "contentType": None, "error": "deployment_not_found"}
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail=f"Audio generation failed for step {step_id}: HTTP {exc.response.status_code}",
                    ) from exc
                except httpx.HTTPError as exc:  # pragma: no cover
                    logger.exception("generateDataStoryAudio request failed for step %s", step_id)
                    raise HTTPException(
                        status_code=502,
                        detail=f"Audio generation request failed for step {step_id}: {exc}",
                    ) from exc

                audio_bytes = await rest_response.aread()
                if not audio_bytes:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Audio generation returned empty audio stream for step {step_id}",
                    )

                content_type = rest_response.headers.get("content-type")
                if not content_type or "audio" not in content_type:
                    content_type = "audio/mpeg"

                audio_segments.append(
                    {
                        "stepId": step_id,
                        "audio": base64.b64encode(audio_bytes).decode("utf-8"),
                        "contentType": content_type,
                    }
                )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("generateDataStoryAudio unexpected failure")
        raise HTTPException(status_code=502, detail=f"Audio generation failed: {exc}") from exc

    if not audio_segments:
        raise HTTPException(status_code=502, detail="Audio generation produced no segments")

    content_type = audio_segments[0].get("contentType") or "audio/mpeg"
    return {"audio": None, "segments": audio_segments, "contentType": content_type}


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "copilotkit-fastapi-runtime",
        "azure_openai_configured": bool(AZURE_OPENAI_API_KEY),
        "tavily_configured": bool(TAVILY_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
