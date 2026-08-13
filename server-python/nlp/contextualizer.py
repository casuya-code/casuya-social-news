"""Contextualizer (Feature #24): news article → dramatic script.

MVP uses a deterministic template generator so the system works without
an LLM API key. The interface mirrors what a real LLM-backed version will
look like, so swapping in `openai` later is a drop-in change.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from nlp.emotion_tagger import tag_line

_CAST: list[dict[str, str]] = [
    {"id": "char_bibi_mkwe", "name": "Bibi Mkwe", "voice_id": "mock_bibi", "mood": "uchangamfu"},
    {"id": "char_mjomba", "name": "Mjomba Juma", "voice_id": "mock_mjomba", "mood": "hasira"},
    {"id": "char_rafiki", "name": "Rafiki Neema", "voice_id": "mock_neema", "mood": "msisimko"},
]

_OPENINGS = [
    "Hujasikia? Mambo yameendelea leo!",
    "Wewe, leo kuna habari kubwa!",
    "Ngoja nikuambie kilichotokea...",
]

_REACTIONS = [
    "Haiwezekani! Kweli ndivyo ilivyo?",
    "Nashangaa sana kusikia hivyo.",
    "Mh... hii inabadilisha mambo mengi.",
    "Lakini sasa, hii ni hatari kweli.",
]

_CLOSINGS = [
    "Basi, tunaendelea kuona mambo yatakavyokuwa.",
    "Tunafuatilia hadithi hii kwa makini.",
    "Na ndivyo ilivyokuwa leo, tusubiri kesho.",
]


def _truncate(headline: str, limit: int = 40) -> str:
    """Chop a headline down for use inside dialogue."""
    return headline if len(headline) <= limit else headline[: limit - 1] + "…"


def build_mock_script(news: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic-but-varied script from a news article dict."""
    headline = _truncate(news.get("headline", "Habari za leo"))
    rng = random.Random(news.get("url", "casuya"))  # same URL → same script

    cast = _CAST[:]
    rng.shuffle(cast)
    cast = cast[:2]  # two speakers per scene for the MVP

    opening = rng.choice(_OPENINGS)
    reaction = rng.choice(_REACTIONS)
    closing = rng.choice(_CLOSINGS)

    lines = [
        {
            "index": 0,
            "character_id": cast[0]["id"],
            "text": f"{opening} {headline}.",
            "emotion": tag_line(0),
            "overlap": False,
        },
        {
            "index": 1,
            "character_id": cast[1]["id"],
            "text": reaction,
            "emotion": tag_line(1),
            "overlap": False,
        },
        {
            "index": 2,
            "character_id": cast[0]["id"],
            "text": closing,
            "emotion": tag_line(2),
            "overlap": False,
        },
    ]

    return {
        "version": "1.0",
        "script_id": uuid4().hex,
        "news_ref": {
            "headline": news.get("headline", ""),
            "source": news.get("source", "unknown"),
            "published_at": news.get("published_at", datetime.now(UTC).isoformat()),
            "url": news.get("url", ""),
        },
        "characters": cast,
        "lines": lines,
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "time_of_day": "mchana",
            "mood_drift_applied": False,
            "characters_delta": 0,
        },
    }


def contextualize(news: dict[str, Any]) -> dict[str, Any]:
    """Entry point: news → script. Swap this for an LLM call later."""
    return build_mock_script(news)
