"""Fetch news and generate scripts from the command line.

Usage:
  python tools/fetch_news.py            # single run
  python tools/fetch_news.py --watch 60 # run every 60 seconds

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

setup_logging()


async def run_once(limit: int) -> int:
    scripts = await ingest_and_generate(limit=limit)
    for script in scripts:
        print(f"[{script['news_ref']['source']}] {script['news_ref']['headline']}")
        print(f"  script_id={script['script_id']} lines={len(script['lines'])}")
    return len(scripts)


async def watch(interval: int, limit: int) -> None:
    while True:
        try:
            await run_once(limit)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            print(f"error: {exc}")
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Casuya news ingestion CLI")
    parser.add_argument("--watch", type=int, default=0, help="run every N seconds")
    parser.add_argument("--limit", type=int, default=10, help="articles per run")
    args = parser.parse_args()

    if args.watch > 0:
        asyncio.run(watch(args.watch, args.limit))
    else:
        asyncio.run(run_once(args.limit))


if __name__ == "__main__":
    main()
