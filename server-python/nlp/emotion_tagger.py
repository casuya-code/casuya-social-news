"""Emotion tagger (Feature #2): assigns [anacheka_kwa_dharau]-style tags to lines."""

from __future__ import annotations

import json
import random
from pathlib import Path

from api.errors import EmotionTaggingError

_TAGS = [
    "anaongea_kwa_huzuni",
    "anacheka_kwa_dharau",
    "anapiga_kelele",
    "anaongea_kwa_utulivu",
    "anashangaa",
    "anafikiria",
    "anakasirika",
    "anahofia",
    "anasikitika",
    "anajigamba",
    "anadhihaki",
]

_INDEX_BASED = {
    0: "anashangaa",  # opening line — surprise/intro
    1: "anafikiria",  # reaction line — thinking
    2: "anaongea_kwa_utulivu",  # closing — calm resolution
}


def _load_registry_tags() -> set[str]:
    """Load the shared emotion-tag registry (contract source of truth)."""
    path = (
        Path(__file__).resolve().parent.parent.parent / "shared" / "schemas" / "emotion_tags.json"
    )
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
        return {entry["tag"] for entry in registry.get("examples", [])}
    except (OSError, ValueError, KeyError, TypeError):
        return set()


def tag_line(index: int, rng: random.Random | None = None) -> str:
    """Return an emotion tag for a line at the given index.

    Opening/reaction/closing lines get deterministic tags; any other line
    picks randomly so scenes vary without an LLM. Raises E1002 if the chosen
    tag is not in the shared registry — the contract must never break.
    """
    if index in _INDEX_BASED:
        tag = _INDEX_BASED[index]
    else:
        rng = rng or random
        tag = rng.choice(_TAGS)

    registry = _load_registry_tags()
    if registry and tag not in registry:
        raise EmotionTaggingError(f"emotion tag '{tag}' is not in the shared registry")
    return tag
