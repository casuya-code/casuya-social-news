"""Character memory and mood drift (Features #22, #25).

After every script, each speaking character:
  - remembers a one-line summary of the story (compressed, retention-safe)
  - accumulates a mood drift value driven by the emotions they performed

These feed back into the contextualizer so later stories feel continuous.
"""

from __future__ import annotations

from typing import Any

# emotion tag -> mood delta in [-1, 1] (valence of the performance)
_MOOD_VALENCE = {
    "anacheka_kwa_dharau": 0.3,
    "anaongea_kwa_huzuni": -0.6,
    "anapiga_kelele": 0.2,
    "anaongea_kwa_utulivu": 0.0,
    "anashangaa": 0.4,
    "anafikiria": 0.0,
    "anakasirika": -0.5,
    "anahofia": -0.4,
    "anasikitika": -0.5,
    "anajigamba": 0.4,
    "anadhihaki": 0.2,
    "anaomba_msaada": -0.3,
}

_DRIFT_DECAY = 0.3  # how much of a single line's emotion moves the baseline


def summarize_script(script: dict[str, Any]) -> dict[str, dict]:
    """Return one-line state per speaking character.

    Format: {"char_id": {"memory": str, "mood": float}}
    """
    headline = script.get("news_ref", {}).get("headline", "habari")
    moods: dict[str, list[float]] = {}
    for line in script.get("lines", []):
        char_id = line.get("character_id", "")
        emotion = line.get("emotion", "")
        moods.setdefault(char_id, []).append(_MOOD_VALENCE.get(emotion, 0.0))

    state: dict[str, dict] = {}
    for char_id, deltas in moods.items():
        mood = sum(deltas) / len(deltas) * _DRIFT_DECAY
        state[char_id] = {"memory": headline, "mood": round(clamp(mood), 3)}
    return state


def apply_drift(current: float, delta: float) -> float:
    """Combine an existing mood with a new script's delta, clamped to [-1, 1]."""
    return round(clamp(current + delta), 3)


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """Clamp a value into [lo, hi]."""
    return max(lo, min(hi, value))


def mood_label(mood: float) -> str:
    """Human label for a mood value (used by the client/UI)."""
    if mood <= -0.5:
        return "hana furaha"  # down
    if mood <= -0.15:
        return "ameguswa"  # slightly down
    if mood >= 0.5:
        return "anafuraha"  # upbeat
    if mood >= 0.15:
        return "ana msisimko"  # slightly up
    return "hali ya kawaida"  # neutral
