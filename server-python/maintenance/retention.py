"""Storage retention (README data-retention rules).

Generated script audio dirs live in storage/ under a 32-hex script_id name.
They are expensive and disposable — purge any dir older than the retention
window (24h by default). Character state and seen-URL JSON files are NOT
script audio and are never touched here.

Run via: python -m maintenance.retention --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from config.settings import get_settings

_SCRIPT_ID_DIR = re.compile(r"^[0-9a-f]{32}$")
_STATE_FILES = {"seen_urls.json", "character_state.json", "votes.json", "mock_round.txt"}

DEFAULT_RETENTION_HOURS = 24


def script_audio_dirs(storage_dir: Path) -> list[Path]:
    """Script-id-named directories that hold generated audio."""
    return [p for p in storage_dir.iterdir() if p.is_dir() and _SCRIPT_ID_DIR.match(p.name)]


def is_expired(path: Path, *, retention_hours: int, now: datetime | None = None) -> bool:
    """A script dir is expired once nothing in it changed within retention."""
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=retention_hours)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return mtime < cutoff


def purge(
    *,
    storage_dir: Path | None = None,
    retention_hours: int = DEFAULT_RETENTION_HOURS,
    dry_run: bool = False,
    now: datetime | None = None,
) -> dict:
    """Delete expired script-audio dirs. Returns a summary dict."""
    storage_dir = storage_dir or get_settings().storage_dir
    removed: list[str] = []
    kept: list[str] = []
    errors: list[str] = []

    for directory in script_audio_dirs(storage_dir):
        if is_expired(directory, retention_hours=retention_hours, now=now):
            removed.append(directory.name)
            if not dry_run:
                try:
                    shutil.rmtree(directory)
                except Exception as exc:  # noqa: BLE001 - report, don't abort
                    errors.append(f"{directory.name}: {exc}")
        else:
            kept.append(directory.name)

    return {
        "purged": len(removed),
        "kept": len(kept),
        "errors": len(errors),
        "removed": removed,
        "kept_dirs": kept,
        "dry_run": dry_run,
        "retention_hours": retention_hours,
        "errors_detail": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Purge expired script audio from storage")
    parser.add_argument("--hours", type=int, default=DEFAULT_RETENTION_HOURS)
    parser.add_argument("--dry-run", action="store_true", help="report only, delete nothing")
    args = parser.parse_args()

    result = purge(retention_hours=args.hours, dry_run=args.dry_run)
    print(
        f"[{'dry-run: ' if result['dry_run'] else ''}purged {result['purged']}, "
        f"kept {result['kept']}, errors {result['errors']}]"
    )
    for name in result["removed"]:
        print(f"  purged: {name}")


if __name__ == "__main__":
    main()
