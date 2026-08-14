"""Celery app: Redis broker + beat for the endless-stories loop.

Production replacement for the in-process :class:`IngestScheduler`. A worker
consumes `run_ingest_cycle` tasks pushed by a beat schedule; the ingest
pipeline itself is untouched. Uses the shared ``redis_url`` as broker and
result backend.
"""

from __future__ import annotations

import asyncio

from celery import Celery

from config.settings import get_settings

_settings = get_settings()

app = Celery(
    "casuya",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["task_queue.celery_app"],
)

app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "ingest-every-cycle": {
            "task": "task_queue.celery_app.run_ingest_cycle",
            "schedule": _settings.scheduler_interval_seconds,
        },
    },
)


@app.task(name="task_queue.celery_app.run_ingest_cycle")
def run_ingest_cycle() -> dict:
    """Run one ingest + generate cycle (executes on the worker)."""
    from scraper.ingestor import ingest_and_generate

    scripts = asyncio.run(ingest_and_generate())
    return {"scripts_generated": len(scripts)}
