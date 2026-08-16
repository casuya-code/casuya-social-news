"""LLM-backed script generator (OpenAI).

When ``OPENAI_API_KEY`` is set the contextualizer delegates to this module,
which asks GPT to write a dramatic Swahili scene that matches the shared
script schema.  If the key is missing or the call fails, the caller falls
back to :func:`nlp.contextualizer.build_mock_script`.
"""

from __future__ import annotations

import json
from typing import Any

from config.logging_config import get_logger
from config.settings import get_settings

_logger = get_logger("nlp.llm")
_settings = get_settings()

_SYSTEM_PROMPT = """\
You are a Swahili radio-drama scriptwriter for Casuya Social News.
Write a short dramatic scene based on a news headline.

RULES:
- Output ONLY valid JSON matching the schema below. No markdown, no commentary.
- Dialogue must be in everyday Swahili (Kiswahili cha mtaa ok).
- Each scene has exactly 3 dialogue lines.
- Characters are drawn from the provided cast list.
- Emotion tags MUST be one of the allowed values.
- Overlap flags: at most one line per scene may be true.
- The "version" field must be exactly "1.0".

SCHEMA:
{
  "version": "1.0",
  "script_id": "<uuid hex>",
  "news_ref": {"headline": "...", "source": "...", "published_at": "...", "url": "..."},
  "characters": [
    {"id": "...", "name": "...", "voice_id": "...", "mood": "...",
     "mood_value": 0.0, "mood_label": "...", "memory": "..."}
  ],
  "lines": [
    {"index": 0, "character_id": "...", "text": "...",
     "emotion": "<emotion_tag>", "overlap": false},
    {"index": 1, "character_id": "...", "text": "...",
     "emotion": "<emotion_tag>", "overlap": false},
    {"index": 2, "character_id": "...", "text": "...",
     "emotion": "<emotion_tag>", "overlap": false}
  ],
  "metadata": {
    "generated_at": "...", "time_of_day": "mchana",
    "mood_drift_applied": false, "characters_delta": 0
  }
}

ALLOWED EMOTION TAGS:
anaongea_kwa_huzuni, anacheka_kwa_dharau, anapiga_kelele,
anaongea_kwa_utulivu, anashangaa, anafikiria, anakasirika,
anahofia, anasikitika, anajigamba, anadhihaki, anaomba_msaada

CHARACTERS (pick 2 for this scene):
"""


def _build_user_prompt(
    news: dict[str, Any],
    cast: list[dict[str, Any]],
    direction: str,
) -> str:
    """Assemble the user message for the LLM."""
    cast_lines = []
    for c in cast:
        mood_val = c.get("mood_value", c.get("mood", 0.0))
        if isinstance(mood_val, str):
            mood_val = 0.0
        cast_lines.append(
            f"- id={c['id']} name={c['name']} voice_id={c['voice_id']} "
            f"mood={c.get('mood', 'utulivu')} mood_value={mood_val} "
            f"mood_label={c.get('mood_label', 'hali ya kawaida')} "
            f"memory={c.get('memory', '')}"
        )
    cast_block = "\n".join(cast_lines)

    return (
        f"NEWS:\nheadline: {news.get('headline', '')}\n"
        f"source: {news.get('source', '')}\n"
        f"url: {news.get('url', '')}\n"
        f"published_at: {news.get('published_at', '')}\n\n"
        f"DIRECTION (community vote): {direction}\n\n"
        f"CHARACTERS:\n{cast_block}\n\n"
        "Write the JSON script now."
    )


def generate_with_llm(
    news: dict[str, Any],
    cast: list[dict[str, Any]],
    direction: str = "utulivu",
) -> dict[str, Any] | None:
    """Ask OpenAI to generate a script. Returns None if unavailable."""
    api_key = _settings.openai_api_key
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        _logger.warning("openai_package_missing")
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=_settings.openai_model,
            temperature=0.8,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(news, cast, direction)},
            ],
        )
        raw = response.choices[0].message.content or ""
        script = json.loads(raw)
        _logger.info("llm_script_generated", model=_settings.openai_model)
        return script
    except json.JSONDecodeError:
        _logger.warning("llm_json_parse_failed")
        return None
    except Exception as exc:  # noqa: BLE001 — any API/network failure → fallback
        _logger.warning("llm_generation_failed", error=str(exc))
        return None
