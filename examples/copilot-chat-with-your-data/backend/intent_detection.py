"""Heuristic intent detection for triggering data story suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

KEY_PHRASES = (
    "how are we doing",
    "how's business",
    "overall performance",
    "overall doing",
    "big picture",
    "summary",
    "recap",
    "performance this month",
    "performance overall",
    "health of",
)


@dataclass
class IntentResult:
    intent: str
    confidence: float
    summary: str
    focus_areas: List[str]


def detect_data_story_intent(message: str) -> IntentResult | None:
    """Return a data story intent when the message matches broad-performance cues."""

    if not message:
        return None

    normalized = message.lower()
    if any(phrase in normalized for phrase in KEY_PHRASES):
        return IntentResult(
            intent="data_story",
            confidence=0.82,
            summary="Walk through the latest dashboard highlights.",
            focus_areas=["revenue", "profit", "products", "regions"],
        )

    return None
