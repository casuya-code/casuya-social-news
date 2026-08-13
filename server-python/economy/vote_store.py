"""File-backed vote store.

Votes must survive process restarts without Postgres/Redis, so they persist
to a JSON file (same pattern as the seen-URL and character-state stores).

Format: {"script_id": {"client_id": "direction"}}
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from config.settings import get_settings

_settings = get_settings()

_lock = threading.Lock()


def votes_path() -> Path:
    """Path to the votes JSON file (inside gitignored storage dir)."""
    return _settings.storage_dir / "votes.json"


def load_votes() -> dict[str, dict[str, str]]:
    """Read persisted votes. Empty dict on any failure."""
    path = votes_path()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:  # noqa: BLE001 - corrupt/missing file → start fresh
        pass
    return {}


def save_votes(votes: dict[str, dict[str, str]]) -> None:
    """Persist votes atomically (write temp, then rename)."""
    path = votes_path()
    tmp = path.with_suffix(".json.tmp")
    try:
        with _lock:
            tmp.write_text(json.dumps(votes, indent=2), encoding="utf-8")
            tmp.replace(path)
    except Exception:  # noqa: BLE001 - never let persistence break voting
        pass
