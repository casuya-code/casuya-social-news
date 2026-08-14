"""Background story scheduler — the endless-stories loop.

Runs `ingest_and_generate` on a timer inside the server process. No Redis
broker or Celery worker needed for local/MVP operation; the loop survives
errors and keeps ticking. Production can swap this for a Celery beat task
without touching the ingest pipeline itself.
"""

from __future__ import annotations

import asyncio
import time

from config.logging_config import get_logger
from monitoring.metrics import (
    SCHEDULER_CYCLES,
    SCHEDULER_ERRORS,
    SCHEDULER_LAST_DURATION,
    SCHEDULER_RUNNING,
)
from scraper.ingestor import ingest_and_generate

_logger = get_logger("task_queue.scheduler")


class IngestScheduler:
    """Periodically pull news and generate dramatic scripts."""

    def __init__(self, interval_seconds: int = 300) -> None:
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self.cycles_completed = 0
        self.stories_generated = 0
        self.last_error: str | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _loop(self) -> None:
        SCHEDULER_RUNNING.set(1)
        while not self._stop_event.is_set():
            cycle_start = time.perf_counter()
            try:
                scripts = await ingest_and_generate()
                self.cycles_completed += 1
                self.stories_generated += len(scripts)
                SCHEDULER_CYCLES.inc()
                _logger.info(
                    "scheduler_cycle",
                    interval=self.interval_seconds,
                    stories=len(scripts),
                    cycles=self.cycles_completed,
                )
            except Exception as exc:  # noqa: BLE001 - keep the loop alive
                self.last_error = str(exc)
                SCHEDULER_ERRORS.inc()
                _logger.error("scheduler_cycle_failed", error=str(exc))
            finally:
                SCHEDULER_LAST_DURATION.set(time.perf_counter() - cycle_start)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                pass  # interval elapsed → run again
        SCHEDULER_RUNNING.set(0)

    async def start(self) -> None:
        """Start the background loop (idempotent)."""
        if self.running:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._loop(), name="ingest-scheduler")

    async def stop(self) -> None:
        """Signal stop and await the loop's clean exit (idempotent)."""
        if self._task is None:
            return
        self._stop_event.set()
        await asyncio.gather(self._task, return_exceptions=True)
        self._task = None

    def snapshot(self) -> dict:
        """Status for health checks / monitoring."""
        return {
            "running": self.running,
            "interval_seconds": self.interval_seconds,
            "cycles_completed": self.cycles_completed,
            "stories_generated": self.stories_generated,
            "last_error": self.last_error,
        }
