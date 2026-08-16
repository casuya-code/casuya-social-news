"""Contextualizer (Feature #24): news article → dramatic script.

MVP uses a deterministic template generator so the system works without
an LLM API key. It weaves in character memory + mood drift (Features #22,
#25) so stories feel continuous. The interface mirrors what a real
LLM-backed version will look like, so swapping in `openai` later is a
drop-in change.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from config.logging_config import get_logger
from nlp.emotion_tagger import tag_line
from nlp.memory import mood_label
from nlp.product_placement import select_placement
from nlp.templates import (
    CAST,
    CLOSINGS,
    CLOSINGS_BY_DIRECTION,
    MEMORY_OPENINGS,
    OPENINGS,
    PROVERBS,
    REACTIONS_NEUTRAL,
    REACTIONS_UPBEAT,
    REACTIONS_WORRIED,
    SLANG_OPENINGS,
)

_logger = get_logger("nlp.contextualizer")

# Tuning constants for mock script generation
SPEAKERS_PER_SCENE = 2
SLANG_PROBABILITY = 0.4
PROVERB_PROBABILITY = 0.35
HEAT_THRESHOLD = 0.4
OVERLAP_REACTION_PROBABILITY = 0.6
OVERLAP_CLOSING_PROBABILITY = 0.3
HEADLINE_TRUNCATE_LIMIT = 40


def _truncate(headline: str, limit: int = HEADLINE_TRUNCATE_LIMIT) -> str:
    """Chop a headline down for use inside dialogue."""
    return headline if len(headline) <= limit else headline[: limit - 1] + "…"


def _reaction_pool(mood: float) -> list[str]:
    """Pick a reaction set tuned to a character's current mood."""
    if mood <= -0.15:
        return REACTIONS_WORRIED
    if mood >= 0.15:
        return REACTIONS_UPBEAT
    return REACTIONS_NEUTRAL


def _carryover_emotion(mood: float, rng: random.Random) -> str:
    """Feature #5: emotion carried over from a character's current mood."""
    if mood <= -0.4:
        return rng.choice(["anakasirika", "anahofia", "anasikitika"])
    if mood >= 0.4:
        return rng.choice(["anajigamba", "anashangaa", "anacheka_kwa_dharau"])
    return tag_line(2)


def build_mock_script(
    news: dict[str, Any],
    cast_state: dict[str, dict] | None = None,
    direction: str = "utulivu",
) -> dict[str, Any]:
    """Create a deterministic script, weaving in memory, mood, and direction."""
    headline = _truncate(news.get("headline", "Habari za leo"))
    rng = random.Random(news.get("url", "casuya") + str(cast_state or {}) + direction)
    cast_state = cast_state or {}

    cast = CAST[:]
    rng.shuffle(cast)
    cast = cast[:SPEAKERS_PER_SCENE]  # two speakers per scene for the MVP

    speaker_a = cast[0]["id"]
    speaker_b = cast[1]["id"]
    state_a = cast_state.get(speaker_a, {"memory": "", "mood": 0.0})
    state_b = cast_state.get(speaker_b, {"memory": "", "mood": 0.0})

    # Feature #26: weave slang into the opening.
    if rng.random() < SLANG_PROBABILITY:
        opening = rng.choice(SLANG_OPENINGS)
        opening_line = f"{opening} {headline}."
    elif state_a.get("memory"):
        opening = rng.choice(MEMORY_OPENINGS)
        opening_line = f"{opening} {headline}."
    else:
        opening = rng.choice(OPENINGS)
        opening_line = f"{opening} {headline}."

    reaction = rng.choice(_reaction_pool(state_b.get("mood", 0.0)))
    direction_pool = CLOSINGS_BY_DIRECTION.get(direction, CLOSINGS)
    closing = rng.choice(direction_pool)

    # Feature #1: sometimes resolve with a methali (proverb) for flavor.
    if rng.random() < PROVERB_PROBABILITY:
        closing = f"{closing} {rng.choice(PROVERBS)}"

    # Feature #5: the closing line carries the speaker's current emotion.
    closing_emotion = _carryover_emotion(state_a.get("mood", 0.0), rng)

    # Feature #6: overlap cues — a heated scene lets lines talk over each other.
    heat = abs(state_a.get("mood", 0.0)) + abs(state_b.get("mood", 0.0))
    overlap_reaction = heat >= HEAT_THRESHOLD and rng.random() < OVERLAP_REACTION_PROBABILITY
    overlap_closing = heat >= HEAT_THRESHOLD and rng.random() < OVERLAP_CLOSING_PROBABILITY

    lines = [
        {
            "index": 0,
            "character_id": speaker_a,
            "text": opening_line,
            "emotion": tag_line(0),
            "overlap": False,
        },
        {
            "index": 1,
            "character_id": speaker_b,
            "text": reaction,
            "emotion": tag_line(1),
            "overlap": overlap_reaction,
        },
        {
            "index": 2,
            "character_id": speaker_a,
            "text": closing,
            "emotion": closing_emotion,
            "overlap": overlap_closing,
        },
    ]

    # Feature #34: append a sponsor sign-off line after the closing.
    placement_line, placement_badge = select_placement(
        news_url=news.get("url", ""),
        cast_state=cast_state,
        speaker=speaker_a,
        next_index=len(lines),
    )
    if placement_line is not None:
        lines.append(placement_line)

    # Expose current mood + memory to the client so the UI can show drift.
    for i, character in enumerate(cast):
        character = dict(character)
        character["mood_value"] = cast_state.get(character["id"], {}).get("mood", 0.0)
        character["mood_label"] = mood_label(character["mood_value"])
        character["memory"] = cast_state.get(character["id"], {}).get("memory", "")
        cast[i] = character

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
            "mood_drift_applied": bool(cast_state),
            "characters_delta": 0,
            **({"product_placement": placement_badge} if placement_badge else {}),
        },
    }


def contextualize(
    news: dict[str, Any],
    cast_state: dict[str, dict] | None = None,
    direction: str = "utulivu",
) -> dict[str, Any]:
    """Entry point: news → script. Uses LLM when OPENAI_API_KEY is set."""
    from nlp.llm_generator import generate_with_llm

    cast_state = cast_state or {}
    cast = [
        {
            "id": c["id"],
            "name": c["name"],
            "voice_id": c["voice_id"],
            "mood": c.get("mood", "utulivu"),
            "mood_value": cast_state.get(c["id"], {}).get("mood", 0.0),
            "mood_label": mood_label(cast_state.get(c["id"], {}).get("mood", 0.0)),
            "memory": cast_state.get(c["id"], {}).get("memory", ""),
        }
        for c in CAST
    ]

    llm_script = generate_with_llm(news, cast, direction)
    if llm_script is not None:
        # Ensure required top-level keys are present (defense against bad LLM output).
        if all(k in llm_script for k in ("version", "script_id", "lines", "characters")):
            return llm_script
        _logger.warning("llm_output_missing_keys", keys=list(llm_script.keys()))

    return build_mock_script(news, cast_state, direction)
