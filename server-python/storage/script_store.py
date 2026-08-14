"""Durable script store (JSON files, one per script_id).

Redis/Postgres are optional in the MVP, so generated scripts must be
retrievable by id after the process restarts. This lets live clients fetch
the full script for a `script_delta` broadcast and play it end-to-end
(listen mode). Files live inside the gitignored storage dir:
  <storage>/scripts/<script_id>.json
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from config.settings import get_settings

_settings = get_settings()

_lock = threading.Lock()


def scripts_dir() -> Path:
    """Directory holding one JSON file per generated script."""
    path = _settings.storage_dir / "scripts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def script_path(script_id: str) -> Path:
    """Path for a single script's JSON file."""
    return scripts_dir() / f"{script_id}.json"


def save_script(script: dict[str, Any]) -> bool:
    """Persist a script atomically. Returns True on success."""
    script_id = script.get("script_id", "")
    if not script_id:
        return False
    path = script_path(script_id)
    tmp = path.with_suffix(".json.tmp")
    try:
        with _lock:
            tmp.write_text(json.dumps(script, indent=2), encoding="utf-8")
            tmp.replace(path)
        return True
    except Exception:  # noqa: BLE001 - never let storage break ingestion
        return False


def load_script(script_id: str) -> dict[str, Any] | None:
    """Read a persisted script by id. None if missing/corrupt."""
    path = script_path(script_id)
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("script_id") == script_id:
                return data
    except Exception:  # noqa: BLE001 - corrupt/missing file → None
        pass
    return None


def list_scripts(limit: int = 20) -> list[dict[str, Any]]:
    """Return the most recently saved scripts (newest first)."""
    try:
        files = sorted(scripts_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:  # noqa: BLE001 - directory unreadable → empty
        return []
    scripts: list[dict[str, Any]] = []
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                scripts.append(data)
                if len(scripts) >= limit:
                    break
        except Exception:  # noqa: BLE001 - skip corrupt file
            continue
    return scripts
