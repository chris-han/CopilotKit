"""Heuristic intent detection for triggering data story suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
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

    normalized = re.sub(r"[^a-z0-9\s]", "", message.lower())

    if any(phrase in normalized for phrase in KEY_PHRASES):
        return IntentResult(
            intent="data_story",
            confidence=0.82,
            summary="Walk through the latest dashboard highlights.",
            focus_areas=["revenue", "profit", "products", "regions"],
        )

    words = normalized.split()
    for phrase in KEY_PHRASES:
        phrase_words = phrase.split()
        if not phrase_words:
            continue

        if len(words) < len(phrase_words):
            ratio = SequenceMatcher(None, normalized, phrase).ratio()
            if ratio >= 0.78:
                return IntentResult(
                    intent="data_story",
                    confidence=0.76,
                    summary="Walk through the latest dashboard highlights.",
                    focus_areas=["revenue", "profit", "products", "regions"],
                )
            continue

        for start in range(0, len(words) - len(phrase_words) + 1):
            window = " ".join(words[start : start + len(phrase_words)])
            ratio = SequenceMatcher(None, window, phrase).ratio()
            if ratio >= 0.78:
                return IntentResult(
                    intent="data_story",
                    confidence=0.76,
                    summary="Walk through the latest dashboard highlights.",
                    focus_areas=["revenue", "profit", "products", "regions"],
                )

    return None
