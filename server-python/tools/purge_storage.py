"""Purge expired script-audio directories from storage.

Usage:
  python tools/purge_storage.py              # delete audio older than 24h
  python tools/purge_storage.py --hours 48   # custom retention
  python tools/purge_storage.py --dry-run    # report only
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from maintenance.retention import DEFAULT_RETENTION_HOURS, run_retention  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full retention sweep")
    parser.add_argument("--hours", type=int, default=DEFAULT_RETENTION_HOURS)
    parser.add_argument("--dry-run", action="store_true", help="report only, delete nothing")
    parser.add_argument("--skip-db", action="store_true", help="audio purge only (no DB access)")
    args = parser.parse_args()

    async def _run() -> dict:
        session = None
        if not args.skip_db:
            try:
                from database.engine import SessionLocal

                session = SessionLocal()
            except Exception:  # noqa: BLE001 - fall back to audio-only
                print("warning: DB unavailable, running audio purge only")
                session = None

        try:
            return await run_retention(
                audio_hours=args.hours,
                dry_run=args.dry_run,
                session=session,
            )
        finally:
            if session is not None:
                try:
                    await session.close()
                except Exception:  # noqa: BLE001
                    pass

    result = asyncio.run(_run())

    prefix = "dry-run: " if result["dry_run"] else ""
    print(
        f"[{prefix}audio purged {result['audio']['purged']}, "
        f"articles deleted {result['articles_deleted']}, "
        f"scripts compressed {result['scripts_compressed']} "
        f"(files dropped {result['script_files_dropped']})]"
    )


if __name__ == "__main__":
    main()
