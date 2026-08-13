"""Durable seen-URL store (JSON file).

Redis and Postgres are optional in the MVP, so URL fingerprints must survive
process restarts. This small file store guarantees the "endless stories" loop
never re-scripts the same story, even with no external services running.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from config.settings import get_settings

_settings = get_settings()

_lock = threading.Lock()


def seen_store_path() -> Path:
    """Path to the seen-URLs JSON file (inside gitignored storage dir)."""
    return _settings.storage_dir / "seen_urls.json"


def load_seen() -> set[str]:
    """Read persisted fingerprints. Returns an empty set on any failure."""
    path = seen_store_path()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(data)
    except Exception:  # noqa: BLE001 - corrupt/missing file → start fresh
        pass
    return set()


def save_seen(fingerprints: set[str]) -> None:
    """Persist fingerprints atomically (write temp, then rename)."""
    path = seen_store_path()
    tmp = path.with_suffix(".json.tmp")
    try:
        with _lock:
            tmp.write_text(
                json.dumps(sorted(fingerprints)),
                encoding="utf-8",
            )
            tmp.replace(path)
    except Exception:  # noqa: BLE001 - never let storage break ingestion
        pass
