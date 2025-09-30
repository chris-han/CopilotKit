"""FastAPI AG-UI runtime powered by Pydantic AI and Tavily."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
import re
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterable, List, Sequence, Tuple
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
    Event,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StepFinishedEvent,
    StepStartedEvent,
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
DATA_STORY_AUDIO_SUMMARY_PROMPT = (
    "You are a professional financial analyst. Identify the most important insight from this section, explain the likely driver in one or two sentences, and cite only the essential numbers. Do not recite table headers or enumerate every row from the markdown table."
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

CHART_TITLES: Dict[str, str] = {
    "sales-overview": "Sales Overview",
    "product-performance": "Product Performance",
    "sales-by-category": "Sales by Category",
    "regional-sales": "Regional Sales",
    "customer-demographics": "Customer Demographics",
}


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


def _format_chart_title(chart_id: str) -> str:
    if chart_id in CHART_TITLES:
        return CHART_TITLES[chart_id]
    # Fallback: humanize the slug
    parts = chart_id.replace("_", "-").split("-")
    return " ".join(part.capitalize() for part in parts if part)


def _inject_chart_suggestions(answer: str, chart_ids: List[str]) -> str:
    if not chart_ids:
        return answer

    unique_ids = list(dict.fromkeys(chart_ids))
    bullet_lines = [f"- [{_format_chart_title(chart_id)}](highlight://{chart_id})" for chart_id in unique_ids]
    lines = answer.splitlines()

    for idx, line in enumerate(lines):
        if line.strip() == "Suggested Charts:":
            # Determine if bullets already follow this heading.
            has_entries = False
            for look_ahead in lines[idx + 1 :]:
                stripped = look_ahead.strip()
                if not stripped:
                    break
                if stripped.startswith("-") or stripped.startswith("*") or re.match(r"\d+\.\s", stripped):
                    has_entries = True
                    break
                # Stop if we reach non-list content.
                break

            if not has_entries:
                lines[idx: idx + 1] = [line, *bullet_lines]
            return "\n".join(lines).strip()

    suffix = [""] if answer.strip() else []
    suggestion_block = ["Suggested Charts:", *bullet_lines]
    return "\n".join([answer.strip(), *suffix, *suggestion_block]).strip()


def _markdown_to_text(markdown: str) -> str:
    if not markdown:
        return ""
    text = re.sub(r"`+", "", markdown)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"[_*]", "", text)
    text = re.sub(r"[>#]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def _story_steps_to_audio_segments(steps: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    segments: List[Dict[str, str]] = []
    for index, step in enumerate(steps, start=1):
        step_id = step.get("id") or f"step-{index}"
        title = step.get("title") or f"Section {index}"
        body_markdown = step.get("markdown", "")
        markdown_lines = body_markdown.splitlines()
        table_lines = [line for line in markdown_lines if "|" in line]
        non_table_markdown = "\n".join(line for line in markdown_lines if "|" not in line)
        body_text = _markdown_to_text(non_table_markdown)
        kpis = step.get("kpis")

        kpi_lines: List[str] = []
        if isinstance(kpis, list):
            for kpi in kpis:
                label = kpi.get("label")
                value = kpi.get("value")
                trend = kpi.get("trend")
                if not label and not value:
                    continue
                trend_suffix = f" (trend: {trend})" if isinstance(trend, str) else ""
                kpi_lines.append(f"- {label or 'Metric'}: {value or 'N/A'}{trend_suffix}")

        default_script = f"Section {index}. {title}. {body_text}".strip()

        talking_points = step.get("talkingPoints")
        if isinstance(talking_points, list) and talking_points:
            for tp_index, point in enumerate(talking_points, start=1):
                talking_point_id = point.get("id") or f"{step_id}-point-{tp_index}"
                point_markdown = str(point.get("markdown", ""))
                point_text = _markdown_to_text(point_markdown) or default_script
                segments.append(
                    {
                        "stepId": step_id,
                        "talkingPointId": talking_point_id,
                        "script": point_text,
                    }
                )
            continue

        summary_text = ""
        try:
            user_sections = [
                f"Step number: {index}",
                f"Step type: {step.get('stepType', 'unknown')}",
                f"Step title: {title}",
            ]
            if body_text:
                user_sections.append(f"Details:\n{body_text}")
            if kpi_lines:
                user_sections.append("Key KPIs:\n" + "\n".join(kpi_lines))
            if table_lines:
                table_rows: List[Dict[str, str]] = []
                header: List[str] = []
                for raw_line in table_lines:
                    stripped_line = raw_line.strip()
                    if not stripped_line:
                        continue
                    if set(stripped_line.replace("|", "").strip()) <= {"-", ":", " "}:
                        continue
                    columns = [col.strip() for col in stripped_line.strip("|").split("|")]
                    if not header:
                        header = [col or f"column_{idx+1}" for idx, col in enumerate(columns)]
                        continue
                    if len(header) == 0:
                        continue
                    row_data: Dict[str, str] = {}
                    for idx, column_name in enumerate(header):
                        row_data[column_name] = columns[idx] if idx < len(columns) else ""
                    table_rows.append(row_data)
                if table_rows:
                    table_json = json.dumps(table_rows, ensure_ascii=False)
                    user_sections.append(
                        "Table data for analysis only (do not read row-by-row):\n" + table_json
                    )
            user_prompt = "\n\n".join(section for section in user_sections if section)

            response = await azure_client.responses.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": DATA_STORY_AUDIO_SUMMARY_PROMPT}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_prompt}],
                    },
                ],
                temperature=0.3,
                max_output_tokens=300,
            )
            summary_text = (response.output_text or "").strip()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to summarize story step %s for audio: %s", step_id, exc)

        script = summary_text or default_script
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


def _wants_event_stream(request: Request) -> bool:
    accept = request.headers.get("accept")
    if not accept:
        return False
    return "text/event-stream" in accept.lower()


async def _synthesize_story_audio(
    script_segments: Sequence[Dict[str, str]],
    *,
    streaming: bool,
    send_event: Callable[[Event], Awaitable[None]] | None = None,
) -> Tuple[List[Dict[str, Any]], str | None, bool, str | None]:
    tts_url = (
        f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{AZURE_OPENAI_TTS_DEPLOYMENT}/audio/speech"
        f"?api-version={AZURE_OPENAI_TTS_API_VERSION}"
    )

    audio_segments: List[Dict[str, Any]] = []
    encountered_error = False
    error_detail: str | None = None
    resolved_content_type: str | None = None
    total_segments = len(script_segments)

    if total_segments == 0:
        encountered_error = True
        error_detail = "story_steps_empty"

    async def emit(event: Event) -> None:
        if send_event is not None:
            await send_event(event)

    if streaming and send_event is not None:
        await emit(StepStartedEvent(stepName="dataStory.audio"))
        await emit(
            CustomEvent(
                type=EventType.CUSTOM,
                name="dataStory.audio.lifecycle",
                value={"totalSegments": total_segments},
            )
        )

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            for index, segment in enumerate(script_segments, start=1):
                step_id = segment.get("stepId") or f"step-{index}"
                talking_point_id = segment.get("talkingPointId")
                narration = segment.get("script") or ""
                segment_step_name = (
                    f"dataStory.audio.segment:{step_id}:{talking_point_id}"
                    if talking_point_id
                    else f"dataStory.audio.segment:{step_id}"
                )

                if streaming and send_event is not None:
                    await emit(StepStartedEvent(stepName=segment_step_name))

                tts_payload = {
                    "model": AZURE_OPENAI_TTS_DEPLOYMENT,
                    "voice": "alloy",
                    "response_format": "mp3",
                    "input": narration,
                    "instructions": DATA_STORY_AUDIO_INSTRUCTIONS,
                }

                rest_response: httpx.Response | None = None
                attempt = 0
                while attempt < 3:
                    attempt += 1
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
                        break
                    except httpx.HTTPStatusError as exc:  # pragma: no cover
                        body_preview = exc.response.text[:200] if exc.response.text else ""
                        logger.warning(
                            "generateDataStoryAudio step %s attempt %s HTTP %s: %s",
                            step_id,
                            attempt,
                            exc.response.status_code,
                            body_preview,
                        )
                        if exc.response.status_code == 404:
                            error_detail = "deployment_not_found"
                            if streaming and send_event is not None:
                                await emit(
                                    CustomEvent(
                                        type=EventType.CUSTOM,
                                        name="dataStory.audio.error",
                                        value={
                                            "code": error_detail,
                                            "stepId": step_id,
                                            "talkingPointId": talking_point_id,
                                            "status": exc.response.status_code,
                                            "message": "TTS deployment not found",
                                        },
                                    )
                                )
                                encountered_error = True
                                rest_response = None
                                break
                            return [], None, True, error_detail
                        if attempt >= 3:
                            detail_message = (
                                f"Audio generation failed for step {step_id}: HTTP {exc.response.status_code}"
                            )
                            if streaming and send_event is not None:
                                await emit(
                                    CustomEvent(
                                        type=EventType.CUSTOM,
                                        name="dataStory.audio.error",
                                        value={
                                            "stepId": step_id,
                                            "talkingPointId": talking_point_id,
                                            "status": exc.response.status_code,
                                            "message": detail_message,
                                        },
                                    )
                                )
                                encountered_error = True
                                rest_response = None
                                break
                            raise HTTPException(
                                status_code=exc.response.status_code,
                                detail=detail_message,
                            ) from exc
                    except httpx.HTTPError as exc:  # pragma: no cover
                        logger.warning(
                            "generateDataStoryAudio request failed for step %s (attempt %s): %s",
                            step_id,
                            attempt,
                            exc,
                        )
                        if attempt >= 3:
                            encountered_error = True
                            if streaming and send_event is not None:
                                await emit(
                                    CustomEvent(
                                        type=EventType.CUSTOM,
                                        name="dataStory.audio.error",
                                        value={
                                            "stepId": step_id,
                                            "talkingPointId": talking_point_id,
                                            "message": "Audio generation request failed",
                                        },
                                    )
                                )
                            rest_response = None
                        else:
                            await asyncio.sleep(0.5 * attempt)
                        if rest_response is None and attempt >= 3:
                            break

                if rest_response is None:
                    if streaming and send_event is not None:
                        await emit(StepFinishedEvent(stepName=segment_step_name))
                    break

                audio_bytes = await rest_response.aread()
                if not audio_bytes:
                    logger.warning("Audio generation returned empty payload for step %s", step_id)
                    encountered_error = True
                    if streaming and send_event is not None:
                        await emit(
                            CustomEvent(
                                type=EventType.CUSTOM,
                                name="dataStory.audio.error",
                                value={
                                    "stepId": step_id,
                                    "talkingPointId": talking_point_id,
                                    "message": "Audio generation returned an empty payload",
                                },
                            )
                        )
                        await emit(StepFinishedEvent(stepName=segment_step_name))
                    break

                content_type = rest_response.headers.get("content-type")
                if not content_type or "audio" not in content_type:
                    content_type = "audio/mpeg"
                resolved_content_type = resolved_content_type or content_type

                audio_segments.append(
                    {
                        "stepId": step_id,
                        "talkingPointId": talking_point_id,
                        "audio": base64.b64encode(audio_bytes).decode("utf-8"),
                        "contentType": content_type,
                    }
                )

                if streaming and send_event is not None:
                    await emit(StepFinishedEvent(stepName=segment_step_name))
                    await emit(
                        CustomEvent(
                            type=EventType.CUSTOM,
                            name="dataStory.audio.progress",
                            value={
                                "stepId": step_id,
                                "talkingPointId": talking_point_id,
                                "completed": index,
                                "total": total_segments if total_segments else 1,
                            },
                        )
                    )

                if encountered_error:
                    break
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("generateDataStoryAudio unexpected failure")
        encountered_error = True
        error_detail = str(exc)
        if streaming and send_event is not None:
            await emit(
                CustomEvent(
                    type=EventType.CUSTOM,
                    name="dataStory.audio.error",
                    value={"message": error_detail},
                )
            )

    if streaming and send_event is not None:
        payload: Dict[str, Any]
        if not audio_segments or encountered_error:
            payload = {
                "segments": [],
                "contentType": resolved_content_type,
                "error": error_detail or "audio_generation_failed",
            }
        else:
            payload = {
                "segments": audio_segments,
                "contentType": resolved_content_type,
            }
        await emit(
            CustomEvent(
                type=EventType.CUSTOM,
                name="dataStory.audio.complete",
                value=payload,
            )
        )
        await emit(StepFinishedEvent(stepName="dataStory.audio"))

    return audio_segments, resolved_content_type, encountered_error, error_detail


def _stream_story_audio(script_segments: Sequence[Dict[str, str]]) -> StreamingResponse:
    event_queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def enqueue(event: Event) -> None:
        await event_queue.put(encoder.encode(event))

    async def runner() -> None:
        try:
            await _synthesize_story_audio(script_segments, streaming=True, send_event=enqueue)
        except HTTPException as exc:
            await enqueue(
                CustomEvent(
                    type=EventType.CUSTOM,
                    name="dataStory.audio.complete",
                    value={
                        "segments": [],
                        "contentType": None,
                        "error": getattr(exc, "detail", "audio_generation_failed"),
                        "status": exc.status_code,
                    },
                )
            )
            await enqueue(StepFinishedEvent(stepName="dataStory.audio"))
        except Exception as exc:  # pragma: no cover
            logger.exception("generateDataStoryAudio unexpected failure during stream")
            await enqueue(
                CustomEvent(
                    type=EventType.CUSTOM,
                    name="dataStory.audio.complete",
                    value={
                        "segments": [],
                        "contentType": None,
                        "error": str(exc),
                    },
                )
            )
            await enqueue(StepFinishedEvent(stepName="dataStory.audio"))
        finally:
            await event_queue.put(None)

    async def event_iterator() -> AsyncIterator[str]:
        worker = asyncio.create_task(runner())
        try:
            while True:
                item = await event_queue.get()
                if item is None:
                    break
                yield item
            await worker
        finally:
            if not worker.done():  # pragma: no branch - defensive cleanup
                worker.cancel()
                with contextlib.suppress(Exception):
                    await worker

    return StreamingResponse(event_iterator(), media_type="text/event-stream")


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
        sanitized_answer = _inject_chart_suggestions(sanitized_answer, chart_ids)
        unique_chart_ids = list(dict.fromkeys(chart_ids))

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

        for chart_id in unique_chart_ids:
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


@app.post("/ag-ui/action/generateStrategicCommentary")
async def action_generate_strategic_commentary() -> Dict[str, Any]:
    prompt = (
        "You are the lead analyst preparing an executive briefing. "
        "Use the dashboard data (sales history, products, categories, regions, demographics, metrics) to write a concise strategic commentary. "
        "Organize the response into three sections titled 'Risks', 'Opportunities', and 'Recommendations'. "
        "Provide two to three bullet points per section, grounded in the data with specific numbers or trends. "
        "Do not include code fences or raw tables. Return valid Markdown only.\n\n"
        f"```json\n{json.dumps(DASHBOARD_CONTEXT)}\n```"
    )

    try:
        result = await analysis_agent.run(prompt)
        commentary = getattr(result, "data", None)
        if commentary is None:
            commentary = getattr(result, "output_text", None)
        if commentary is None:
            commentary = str(result)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to generate strategic commentary")
        raise HTTPException(status_code=500, detail=f"Strategic commentary error: {exc}") from exc

    return {"commentary": commentary}


@app.post("/ag-ui/action/generateDataStoryAudio")
async def action_generate_data_story_audio(request: Request) -> Response:
    if not DATA_STORY_AUDIO_ENABLED:
        raise HTTPException(status_code=503, detail="Audio narration disabled")

    request_payload = await request.json()
    steps = request_payload.get("steps")
    if not isinstance(steps, list) or not steps:
        steps = generate_data_story_steps()

    wants_stream = _wants_event_stream(request)

    script_segments = await _story_steps_to_audio_segments(steps)
    if not script_segments:
        if wants_stream:
            return _stream_story_audio(script_segments)
        raise HTTPException(status_code=400, detail="Story steps are empty")

    if wants_stream:
        return _stream_story_audio(script_segments)

    audio_segments, content_type, encountered_error, error_detail = await _synthesize_story_audio(
        script_segments,
        streaming=False,
    )

    if encountered_error or not audio_segments:
        logger.warning("Audio generation encountered an error; returning without narration")
        error_code = error_detail or "audio_generation_failed"
        return JSONResponse(
            {"audio": None, "segments": [], "contentType": None, "error": error_code},
            status_code=200,
        )

    resolved_type = content_type or audio_segments[0].get("contentType") or "audio/mpeg"
    return JSONResponse({"audio": None, "segments": audio_segments, "contentType": resolved_type})


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
