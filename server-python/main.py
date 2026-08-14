"""Casuya Social News server entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

from api.handlers import register_exception_handlers
from api.routes.v1.router import api_v1_router
from config.logging_config import setup_logging
from config.settings import get_settings
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.request_id import RequestIDMiddleware
from monitoring.metrics import MetricsMiddleware, render_metrics
from task_queue.scheduler import IngestScheduler

setup_logging()

_settings = get_settings()
scheduler = IngestScheduler(interval_seconds=_settings.scheduler_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Ensure storage directory exists for audio assets.
    _settings.storage_dir.mkdir(parents=True, exist_ok=True)
    if _settings.scheduler_enabled:
        await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


app = FastAPI(
    title="Casuya Social News",
    version="0.1.0",
    description="Real-time Swahili social news drama engine (server).",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(MetricsMiddleware)  # outermost → sees every request/response

# Serve synthesized audio from local storage.
os.makedirs(_settings.storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=_settings.storage_dir), name="storage")

app.include_router(api_v1_router)


@app.get("/")
async def root() -> dict:
    """Simple root route for sanity checks."""
    return {"service": "casuya-social-news", "docs": "/docs"}


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape endpoint (no API key — scoped to the scrape target)."""
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
