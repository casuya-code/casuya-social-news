"""File-backed character state store.

Persistence for each character's current memory + mood so continuity
survives process restarts without Postgres/Redis (same pattern as the
seen-URL store). Format:
  {"char_id": {"memory": str, "mood": float}}
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from config.settings import get_settings

_settings = get_settings()

_lock = threading.Lock()
_default_state = {"memory": "", "mood": 0.0}


def state_path() -> Path:
    """Path to the character-state JSON file (inside gitignored storage dir)."""
    return _settings.storage_dir / "character_state.json"


def load_states() -> dict[str, dict[str, Any]]:
    """Read persisted character states. Empty dict on any failure."""
    path = state_path()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:  # noqa: BLE001 - corrupt/missing file → start fresh
        pass
    return {}


def save_states(states: dict[str, dict[str, Any]]) -> None:
    """Persist character states atomically."""
    path = state_path()
    tmp = path.with_suffix(".json.tmp")
    try:
        with _lock:
            tmp.write_text(json.dumps(states, indent=2), encoding="utf-8")
            tmp.replace(path)
    except Exception:  # noqa: BLE001 - never let persistence break the loop
        pass


def get_state(character_id: str) -> dict[str, Any]:
    """Return the state for a character (or a fresh default)."""
    states = load_states()
    return states.get(character_id, dict(_default_state))


def set_states(updates: dict[str, dict[str, Any]]) -> None:
    """Merge updates into the persisted store."""
    states = load_states()
    states.update(updates)
    save_states(states)
