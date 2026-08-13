"""Delta compression for live scene/character updates (Feature #27).

Instead of pushing full scripts to every connected client, we diff each
character's state (mood, memory) against what the client already has and
send only the changed fields. Keeps the WebSocket payload tiny on mobile.
"""

from __future__ import annotations

from typing import Any


def build_character_delta(characters: list[dict], prev_states: dict[str, dict]) -> list[dict]:
    """Return only the characters whose state actually changed.

    Each entry carries the stable identity plus any changed fields.
    """
    deltas: list[dict] = []
    for character in characters:
        char_id = character.get("id", "")
        previous = prev_states.get(char_id, {})

        change: dict[str, Any] = {"id": char_id, "name": character.get("name", char_id)}

        new_mood = character.get("mood_value", 0.0)
        if new_mood != previous.get("mood", 0.0):
            change["mood"] = new_mood
            change["mood_label"] = character.get("mood_label", "")

        new_memory = character.get("memory", "")
        if new_memory and new_memory != previous.get("memory", ""):
            change["memory"] = new_memory

        if len(change) > 2:  # identity + at least one changed field
            deltas.append(change)
    return deltas


def build_script_delta(script: dict, prev_states: dict[str, dict]) -> dict[str, Any]:
    """Compact live-update message for one generated script."""
    character_deltas = build_character_delta(script.get("characters", []), prev_states)
    script["metadata"]["characters_delta"] = len(character_deltas)
    return {
        "type": "script_delta",
        "script_id": script["script_id"],
        "headline": script.get("news_ref", {}).get("headline", ""),
        "time_of_day": script.get("metadata", {}).get("time_of_day", ""),
        "characters_delta": character_deltas,
    }
