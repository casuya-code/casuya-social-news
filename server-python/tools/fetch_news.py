"""Fetch news and generate scripts from the command line.

Usage:
  python tools/fetch_news.py                    # single run
  python tools/fetch_news.py --watch 60         # run every 60 seconds
  python tools/fetch_news.py --rotate           # fresh stories each run
  python tools/fetch_news.py --reset --rotate   # fresh demo w/ continuity

Runs the ingest → generate pipeline directly (no server required).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.logging_config import setup_logging  # noqa: E402
from scraper.ingestor import ingest_and_generate  # noqa: E402
from scraper.mock_feed import MockFeed  # noqa: E402

setup_logging()


async def run_once(limit: int, rotate: bool) -> int:
    feed = MockFeed(rotate=rotate)
    scripts = await ingest_and_generate(fetcher=feed, limit=limit)
    for script in scripts:
        print(f"[{script['news_ref']['source']}] {script['news_ref']['headline']}")
        print(f"  script_id={script['script_id']} lines={len(script['lines'])}")
        for line in script["lines"]:
            print(f"    - {line['text'][:70]}")
    return len(scripts)


async def watch(interval: int, limit: int, rotate: bool) -> None:
    while True:
        try:
            await run_once(limit, rotate)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            print(f"error: {exc}")
        await asyncio.sleep(interval)


def reset_state() -> None:
    """Clear seen URLs, character memory, and the mock round counter."""
    from nlp.character_state import state_path
    from scraper.mock_feed import MockFeed
    from scraper.seen_store import seen_store_path

    for path in (seen_store_path(), state_path(), MockFeed._round_file()):
        try:
            path.unlink(missing_ok=True)
            print(f"cleared: {path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"could not clear {path.name}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Casuya news ingestion CLI")
    parser.add_argument("--watch", type=int, default=0, help="run every N seconds")
    parser.add_argument("--limit", type=int, default=10, help="articles per run")
    parser.add_argument("--rotate", action="store_true", help="fresh stories each run")
    parser.add_argument("--reset", action="store_true", help="clear seen URLs and character memory")
    args = parser.parse_args()

    if args.reset:
        reset_state()

    if args.watch > 0:
        asyncio.run(watch(args.watch, args.limit, args.rotate))
    else:
        asyncio.run(run_once(args.limit, args.rotate))


if __name__ == "__main__":
    main()
