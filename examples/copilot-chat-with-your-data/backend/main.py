"""FastAPI AG-UI runtime powered by Pydantic AI and Tavily."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
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
from lida_enhanced_manager import LidaEnhancedManager, create_lida_enhanced_manager
from focus_sample_data_integration import create_focus_sample_integration, FocusSampleDataIntegration

load_dotenv()


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=None)
def _load_prompt(filename: str) -> str:
    """Read prompt text from the prompts directory with basic caching."""

    path = PROMPTS_DIR / filename
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:  # pragma: no cover - configuration guard
        raise RuntimeError(f"Prompt file not found: {path}") from exc


AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-04-01-preview")
AZURE_OPENAI_TTS_DEPLOYMENT = os.getenv("AZURE_OPENAI_TTS_DEPLOYMENT") or "gpt-4o-mini-tts"
AZURE_OPENAI_TTS_API_VERSION = os.getenv("AZURE_OPENAI_TTS_API_VERSION", "2025-03-01-preview")
DATA_STORY_AUDIO_ENABLED = (os.getenv("DATA_STORY_AUDIO_ENABLED", "true").lower() not in {"false", "0", "no"})
ANALYSIS_AGENT_SYSTEM_PROMPT = _load_prompt("analysis_agent_system_prompt.md")
DATA_STORY_AUDIO_INSTRUCTIONS = _load_prompt("data_story_audio_instructions.md")
STRATEGIC_COMMENTARY_PROMPT = _load_prompt("strategic_commentary_prompt.md")
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
    system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT,
)

encoder = EventEncoder()

DATA_STORY_INTENTS: Dict[str, Dict[str, Any]] = {}

# Global LIDA Enhanced Manager instance (initialized on first use)
_lida_manager: Optional[LidaEnhancedManager] = None

# Global FOCUS Sample Data Integration instance (initialized on first use)
_focus_integration: Optional[FocusSampleDataIntegration] = None


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
                lead_in = str(point.get("audioLeadIn", "")).strip()
                if lead_in:
                    if point_text:
                        point_text = f"{lead_in} {point_text}".strip()
                    else:
                        point_text = lead_in
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
                "Task: audio_summary",
                "Audience: executive stakeholders who care most about the strategic takeaway. Provide at most two sentences with confident tone.",
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
                        "content": [{"type": "text", "text": STRATEGIC_COMMENTARY_PROMPT}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_prompt}],
                    },
                ],
                temperature=0.3,
                max_output_tokens=250,
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


@app.get("/ag-ui/dashboard-data")
async def stream_dashboard_data() -> StreamingResponse:
    """Stream the dashboard dataset as a server-sent events feed."""

    async def event_stream() -> AsyncIterator[str]:
        payload = json.dumps(DASHBOARD_CONTEXT)
        yield f"data: {payload}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


async def _generate_strategic_commentary_markdown() -> str:
    """Run the strategic commentary agent and return markdown output."""

    prompt = (
        f"{STRATEGIC_COMMENTARY_PROMPT}\n\n"
        f"```json\n{json.dumps(DASHBOARD_CONTEXT)}\n```"
    )

    result = await analysis_agent.run(prompt)
    commentary = getattr(result, "data", None)
    if commentary is None:
        commentary = getattr(result, "output_text", None)
    if commentary is None:
        commentary = str(result)

    commentary_text = str(commentary).strip()
    if not commentary_text:
        raise ValueError("Strategic commentary agent returned empty output")
    return commentary_text


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

    try:
        strategic_commentary = await _generate_strategic_commentary_markdown()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to generate strategic commentary for data story")
        raise HTTPException(status_code=500, detail=f"Strategic commentary error: {exc}") from exc

    steps = generate_data_story_steps(strategic_commentary)
    info = DATA_STORY_INTENTS.get(intent_id or "")

    response: Dict[str, Any] = {
        "storyId": intent_id or f"story-{uuid4()}",
        "steps": steps,
        "strategicCommentary": strategic_commentary,
    }

    if info:
        response["summary"] = info.get("summary")
        response["focusAreas"] = info.get("focusAreas")
        DATA_STORY_INTENTS.pop(intent_id or "", None)

    return response


@app.post("/ag-ui/action/generateStrategicCommentary")
async def action_generate_strategic_commentary() -> Dict[str, Any]:
    try:
        commentary = await _generate_strategic_commentary_markdown()
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
    commentary_hint = request_payload.get("strategicCommentary")
    strategic_commentary = (
        commentary_hint.strip() if isinstance(commentary_hint, str) and commentary_hint.strip() else None
    )

    if not isinstance(steps, list) or not steps:
        if strategic_commentary is None:
            try:
                strategic_commentary = await _generate_strategic_commentary_markdown()
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to regenerate strategic commentary for audio story")
                raise HTTPException(status_code=500, detail=f"Strategic commentary error: {exc}") from exc
        steps = generate_data_story_steps(strategic_commentary)

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


async def _get_lida_manager() -> LidaEnhancedManager:
    """Get or create the global LIDA Enhanced Manager instance."""
    global _lida_manager
    if _lida_manager is None:
        _lida_manager = await create_lida_enhanced_manager(
            azure_client=azure_client,
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            dashboard_context=DASHBOARD_CONTEXT
        )
    return _lida_manager


async def _get_focus_integration() -> FocusSampleDataIntegration:
    """Get or create the global FOCUS Sample Data Integration instance."""
    global _focus_integration
    if _focus_integration is None:
        # Get LIDA manager instance to pass to FOCUS integration
        lida_manager = await _get_lida_manager()
        _focus_integration = await create_focus_sample_integration(lida_manager=lida_manager)

        # Pre-generate sample datasets
        await _focus_integration.generate_sample_dataset(
            dataset_name="small_company_finops",
            num_records=500
        )
        await _focus_integration.generate_sample_dataset(
            dataset_name="enterprise_multi_cloud",
            num_records=2000
        )
        await _focus_integration.generate_sample_dataset(
            dataset_name="startup_aws_only",
            num_records=100
        )

    return _focus_integration


@app.post("/ag-ui/action/lidaEnhancedAnalysis")
async def action_lida_enhanced_analysis(request: Request) -> Dict[str, Any]:
    """
    AG-UI action for LIDA-enhanced analysis.

    This endpoint integrates LIDA intelligence with existing AG-UI functionality,
    providing enhanced chart recommendations and semantic insights.
    """
    try:
        payload = await request.json()
        query = payload.get("query", "")
        thread_id = payload.get("threadId", "")
        persona = payload.get("persona", "analyst")

        if not query:
            raise HTTPException(status_code=400, detail="Missing query parameter")

        logger.info("lidaEnhancedAnalysis invoked (query=%s, persona=%s)", query, persona)

        # Get LIDA manager instance
        lida_manager = await _get_lida_manager()

        # Create enhanced data summary
        data_summary = await lida_manager.summarize_data(
            data=DASHBOARD_CONTEXT,
            summary_method="default"
        )

        # Generate LIDA goals based on query and persona
        goals = await lida_manager.generate_goals(
            summary=data_summary,
            n=3,
            persona=persona
        )

        # Create visualization specifications
        viz_specs = []
        chart_recommendations = []

        for goal in goals:
            viz_spec = await lida_manager.visualize_goal(goal, data_summary)
            viz_specs.append(viz_spec)

            # Extract chart IDs for AG-UI highlighting
            chart_ids = viz_spec.get("ag_ui_highlight", {}).get("chart_ids", [])
            chart_recommendations.extend(chart_ids)

        # Remove duplicates while preserving order
        unique_chart_recommendations = list(dict.fromkeys(chart_recommendations))

        # Run enhanced analysis with existing agent (preserving current functionality)
        latest_user, system_messages, transcript = _extract_prompt_details([
            {"role": "user", "content": query}
        ])

        # Enhance prompt with LIDA context
        enhanced_prompt_sections = [
            ANALYSIS_AGENT_SYSTEM_PROMPT,
            f"LIDA Enhanced Context:\nData Summary: {data_summary.summary}",
            f"Generated Goals: {[goal.question for goal in goals]}",
            f"Key Insights: {'; '.join(data_summary.insights)}",
            f"Persona: {persona}",
            f"Latest user request: {query}",
            f"Dashboard context: {json.dumps(DASHBOARD_CONTEXT)}"
        ]

        enhanced_prompt = "\n\n".join(enhanced_prompt_sections)
        result = await analysis_agent.run(enhanced_prompt)

        enhanced_analysis = getattr(result, "data", None)
        if enhanced_analysis is None:
            enhanced_analysis = getattr(result, "output_text", None)
        if enhanced_analysis is None:
            enhanced_analysis = str(result)

        return {
            "enhanced_analysis": enhanced_analysis,
            "recommended_charts": unique_chart_recommendations,
            "lida_goals": [goal.dict() for goal in goals],
            "data_insights": data_summary.insights,
            "visualization_specs": viz_specs,
            "semantic_summary": data_summary.summary,
            "persona": persona,
            "thread_id": thread_id
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("LIDA enhanced analysis failed")
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc


@app.get("/finops-web/datasets")
async def get_focus_datasets() -> Dict[str, Any]:
    """
    Get list of available FOCUS sample datasets.

    Returns dataset metadata including compliance scores, record counts,
    and other information needed by the frontend DatasetSelector component.
    """
    try:
        focus_integration = await _get_focus_integration()
        datasets_info = await focus_integration.get_available_datasets()

        # Transform to match frontend expectations
        transformed_datasets = []
        for dataset in datasets_info:
            # Add FinOps-specific metadata
            transformed_dataset = {
                "name": dataset["name"],
                "description": dataset.get("description", f"FOCUS-compliant FinOps dataset with {dataset['record_count']} records"),
                "rows": dataset["record_count"],
                "compliance_score": dataset.get("focus_compliance_score", 0.95),  # High compliance for generated data
                "dataset_type": "focus_sample",
                "service_count": dataset.get("unique_services", 12),
                "account_count": dataset.get("unique_accounts", 3),
                "region_count": dataset.get("unique_regions", 4),
                "data_quality_score": dataset.get("data_quality_score", 0.92),
                "optimization_opportunities_count": dataset.get("optimization_opportunities", 8),
                "anomaly_candidates_count": dataset.get("anomaly_candidates", 2),
            }
            transformed_datasets.append(transformed_dataset)

        return {"datasets": transformed_datasets}

    except Exception as exc:
        logger.exception("Failed to get FOCUS datasets")
        raise HTTPException(status_code=500, detail=f"Dataset retrieval error: {exc}") from exc


@app.post("/finops-web/select-dataset")
async def select_focus_dataset(request: Request) -> Dict[str, Any]:
    """
    Select and load a specific FOCUS dataset for analysis.

    Returns dataset preview data and metadata for the frontend components.
    """
    try:
        payload = await request.json()
        user_id = payload.get("user_id", "web_user")
        dataset_name = payload.get("dataset_name")

        if not dataset_name:
            raise HTTPException(status_code=400, detail="Missing dataset_name parameter")

        logger.info("Selecting FOCUS dataset '%s' for user '%s'", dataset_name, user_id)

        focus_integration = await _get_focus_integration()

        # Get dataset in LIDA-compatible format
        lida_dataset = await focus_integration.get_dataset_for_lida(dataset_name)

        # Create preview data (first 10 records)
        sample_records = lida_dataset["sample_data"][:10] if len(lida_dataset["sample_data"]) > 10 else lida_dataset["sample_data"]

        # Extract column names from the first record
        columns = list(sample_records[0].keys()) if sample_records else []

        # Generate basic statistics for numeric columns
        statistics = {}
        if sample_records:
            for column in columns:
                values = [record.get(column) for record in lida_dataset["sample_data"] if record.get(column) is not None]
                if values and all(isinstance(v, (int, float)) for v in values[:10]):  # Check first 10 values
                    numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                    if numeric_values:
                        statistics[column] = {
                            "min": min(numeric_values),
                            "max": max(numeric_values),
                            "mean": sum(numeric_values) / len(numeric_values),
                            "count": len(numeric_values)
                        }

        # Build response matching frontend expectations
        response = {
            "dataset": {
                "name": dataset_name,
                "description": lida_dataset.get("description", "FOCUS-compliant FinOps dataset for cost analysis and optimization"),
                "rows": lida_dataset.get("row_count", len(lida_dataset["sample_data"])),
                "compliance_score": 0.95,
                "data_quality_score": 0.92,
            },
            "preview": {
                "columns": columns,
                "sample_records": sample_records,
                "statistics": statistics,
            }
        }

        logger.info("Successfully selected FOCUS dataset '%s' with %d records", dataset_name, lida_dataset.get("row_count", len(lida_dataset["sample_data"])))
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to select FOCUS dataset")
        raise HTTPException(status_code=500, detail=f"Dataset selection error: {exc}") from exc


@app.post("/lida/visualize")
async def lida_visualize(request: Request) -> Dict[str, Any]:
    """
    Generate LIDA visualizations based on natural language goals.

    This endpoint integrates with the LIDA Enhanced Manager to create
    visualizations from user goals and selected datasets.
    """
    try:
        payload = await request.json()
        dataset_name = payload.get("dataset_name")
        goal = payload.get("goal")
        chart_type = payload.get("chart_type")
        persona = payload.get("persona", "default")
        summary = payload.get("summary", {})

        if not dataset_name:
            raise HTTPException(status_code=400, detail="Missing dataset_name parameter")
        if not goal:
            raise HTTPException(status_code=400, detail="Missing goal parameter")

        logger.info("LIDA visualize request: dataset=%s, goal=%s, chart_type=%s, persona=%s",
                   dataset_name, goal, chart_type, persona)

        # Get LIDA manager and FOCUS integration instances
        lida_manager = await _get_lida_manager()
        focus_integration = await _get_focus_integration()

        # Get the dataset for LIDA processing
        lida_dataset = await focus_integration.get_dataset_for_lida(dataset_name)

        # Create enhanced data summary from the dataset
        data_summary = await lida_manager.summarize_data(
            data=lida_dataset,
            summary_method="default"
        )

        # For now, create a simplified visualization without full LIDA complexity
        # TODO: Integrate with full LIDA pipeline when ready

        # Generate ECharts configuration using the ECharts adapter
        from echarts_lida_adapter import create_echarts_lida_adapter
        echarts_adapter = await create_echarts_lida_adapter()

        # Determine chart type
        final_chart_type = chart_type if chart_type and chart_type != "auto" else "bar"

        # Create a goal dictionary for the ECharts adapter
        goal_dict = {
            "question": goal,
            "visualization": final_chart_type,
            "rationale": f"User requested {final_chart_type} visualization for: {goal}"
        }

        # Create data summary for the adapter
        data_summary_dict = {
            "summary": f"FOCUS dataset with {lida_dataset.get('row_count', 0)} records",
            "field_names": list(lida_dataset.get("columns", [])),
            "data": lida_dataset["sample_data"][:50],  # Use first 50 records for performance
            "insights": [
                f"Dataset contains {lida_dataset.get('row_count', 0)} records",
                f"Analyzing {len(lida_dataset.get('columns', []))} different metrics"
            ]
        }

        # Generate visualization using the ECharts adapter
        viz_result = await echarts_adapter.generate_visualization(
            goal=goal_dict,
            data_summary=data_summary_dict,
            persona=persona
        )

        echarts_config = viz_result.get("chart_config", {})

        # Generate insights from the data
        insights = []
        if hasattr(data_summary, 'insights'):
            insights = data_summary.insights
        else:
            # Generate basic insights from the dataset
            insights = [
                f"Dataset contains {lida_dataset.get('row_count', 0)} records",
                f"Analyzing {len(lida_dataset.get('columns', []))} different metrics",
                f"Data covers the period from {lida_dataset.get('focus_metadata', {}).get('date_range', {}).get('start', 'N/A')} to {lida_dataset.get('focus_metadata', {}).get('date_range', {}).get('end', 'N/A')}"
            ]

        # Create Python/JavaScript code for the visualization
        code = f"""
# LIDA Generated Visualization Code
import echarts from 'echarts';

const chartConfig = {echarts_config};

const chart = echarts.init(document.getElementById('chart-container'));
chart.setOption(chartConfig);
"""

        # Build response in expected format
        response = {
            "visualizations": [{
                "explanation": f"Visualization showing {goal}",
                "chart_config": echarts_config,
                "code": code,
                "chart_type": final_chart_type,
                "goal": goal,
                "persona": persona
            }],
            "insights": insights,
            "data_summary": {
                "total_records": lida_dataset.get("row_count", 0),
                "columns": list(lida_dataset.get("columns", [])),
                "dataset_type": lida_dataset.get("type", "focus_finops")
            }
        }

        logger.info("Successfully generated LIDA visualization for goal: '%s'", goal)
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("LIDA visualization generation failed")
        raise HTTPException(status_code=500, detail=f"Visualization error: {exc}") from exc


@app.post("/lida/upload")
async def lida_upload_file(request: Request) -> Dict[str, Any]:
    """
    Handle file uploads for LIDA processing.

    This endpoint accepts CSV file uploads and processes them for
    LIDA visualization generation.
    """
    try:
        # For now, return a placeholder response
        # TODO: Implement actual file upload processing
        raise HTTPException(status_code=501, detail="File upload not yet implemented. Please use sample datasets instead.")

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("LIDA file upload failed")
        raise HTTPException(status_code=500, detail=f"Upload error: {exc}") from exc


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
