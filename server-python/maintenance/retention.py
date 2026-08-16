"""Storage + database retention (README data-retention rules).

- Script audio dirs: purge any 32-hex dir older than the window (24h).
- Raw news articles: delete DB rows older than the window (48h regardless).
- Full script JSON: after 24h compress the DB row to a one-line summary
  (`Script.summary`) and remove the original payload; drop the file-backed
  script from the durable store so listen-mode clients can't resurrect
  expired scripts.

Character state, mood values, and seen-URL fingerprints are never touched
(they are cheap, high-value, indefinite retention).

Run via: python -m maintenance.retention --dry-run
"""

from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select

from config.settings import get_settings

_SCRIPT_ID_DIR = re.compile(r"^[0-9a-f]{32}$")
_STATE_FILES = {"seen_urls.json", "character_state.json", "votes.json", "mock_round.txt"}

DEFAULT_RETENTION_HOURS = 24
DEFAULT_ARTICLE_HOURS = 48
DEFAULT_SCRIPT_HOURS = 24


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


def _one_line_summary(script: dict) -> str:
    """Compact a full script into a single storage-friendly line."""
    headline = script.get("news_ref", {}).get("headline", "habari")
    cast = len(script.get("characters", []))
    lines = len(script.get("lines", []))
    return f"{headline} | wahusika {cast}, mistari {lines}"


async def purge_expired_articles(
    session,
    *,
    retention_hours: int = DEFAULT_ARTICLE_HOURS,
    now: datetime | None = None,
) -> int:
    """Delete raw news article rows older than the window. Returns count."""
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=retention_hours)
    try:
        from database.models import NewsArticle

        result = await session.execute(
            delete(NewsArticle).where(NewsArticle.fetched_at < cutoff)
        )
        await session.commit()
        return int(result.rowcount or 0)
    except Exception:  # noqa: BLE001 - DB down → retention degrades
        await session.rollback()
        return 0


async def compress_old_scripts(
    session,
    *,
    retention_hours: int = DEFAULT_SCRIPT_HOURS,
    now: datetime | None = None,
) -> dict:
    """Compress full script JSON to one-line summaries after the window.

    Updates the DB row (summary set, full_json emptied) and removes the
    file-backed copy so expired scripts can't be resurrected by id.
    Returns {"compressed": n, "files_dropped": n}.
    """
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=retention_hours)
    compressed = 0
    files_dropped = 0
    try:
        from database.models import Script
        from storage.script_store import script_path

        rows = (
            await session.execute(
                select(Script)
                .where(Script.created_at < cutoff)
                .where(Script.summary.is_(None))
            )
        ).scalars()
        for script in rows:
            try:
                script.summary = _one_line_summary(script.full_json or {})
                script.full_json = {}
                compressed += 1
                path = script_path(script.id)
                if path.exists():
                    path.unlink()
                    files_dropped += 1
            except Exception:  # noqa: BLE001 - keep sweeping the rest
                continue
        await session.commit()
    except Exception:  # noqa: BLE001 - DB down → retention degrades
        await session.rollback()
        return {"compressed": 0, "files_dropped": 0}
    return {"compressed": compressed, "files_dropped": files_dropped}


async def run_retention(
    *,
    storage_dir: Path | None = None,
    audio_hours: int = DEFAULT_RETENTION_HOURS,
    article_hours: int = DEFAULT_ARTICLE_HOURS,
    script_hours: int = DEFAULT_SCRIPT_HOURS,
    dry_run: bool = False,
    now: datetime | None = None,
    session=None,
) -> dict:
    """Run the full retention sweep: audio dirs + DB articles + script JSON."""
    audio = purge(
        storage_dir=storage_dir,
        retention_hours=audio_hours,
        dry_run=dry_run,
        now=now,
    )
    if dry_run or session is None:
        articles = {"deleted": 0}
        scripts = {"compressed": 0, "files_dropped": 0}
    else:
        articles = {
            "deleted": await purge_expired_articles(
                session, retention_hours=article_hours, now=now
            )
        }
        scripts = await compress_old_scripts(session, retention_hours=script_hours, now=now)

    return {
        "audio": {k: audio[k] for k in ("purged", "kept", "dry_run")},
        "articles_deleted": articles["deleted"],
        "scripts_compressed": scripts["compressed"],
        "script_files_dropped": scripts["files_dropped"],
        "dry_run": dry_run,
    }
