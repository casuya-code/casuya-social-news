"""Casuya Social News server entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.handlers import register_exception_handlers
from api.routes.v1.router import api_v1_router
from config.logging_config import setup_logging
from config.settings import get_settings
from database.engine import check_schema_version
from database.seed import seed_admin_user, seed_characters
from middleware.body_limit import BodySizeLimitMiddleware
from middleware.rate_limiter import RateLimiterMiddleware
from middleware.request_id import RequestIDMiddleware
from middleware.response_envelope import ResponseEnvelopeMiddleware
from monitoring.metrics import MetricsMiddleware, render_metrics
from task_queue.scheduler import IngestScheduler

setup_logging()

_settings = get_settings()
scheduler = IngestScheduler(
    interval_seconds=_settings.scheduler_interval_seconds,
    retention_cycle_frequency=_settings.retention_cycle_frequency,
    retention_enabled=_settings.retention_enabled,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Ensure storage directory exists for audio assets.
    _settings.storage_dir.mkdir(parents=True, exist_ok=True)
    _settings.validate_production_secrets()
    await check_schema_version()
    await seed_characters()
    await seed_admin_user()
    app.state.scheduler = scheduler
    if _settings.scheduler_enabled and _settings.scheduler_backend == "inprocess":
        await scheduler.start()
    elif _settings.scheduler_backend == "celery":
        import logging
        logging.getLogger("casuya.startup").info(
            "Celery mode: run 'celery -A task_queue.celery_app worker -B' separately"
        )
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

if _settings.allowed_origins:
    origins = [o.strip() for o in _settings.allowed_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(ResponseEnvelopeMiddleware)
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(MetricsMiddleware)  # outermost → sees every request/response

# Serve synthesized audio from local storage.
os.makedirs(_settings.storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=_settings.storage_dir), name="storage")

app.include_router(api_v1_router)

# Serve the Godot web export if it has been built.
_WEB_EXPORT_DIR = Path(__file__).resolve().parent.parent / "client-godot" / "build" / "web"
if _WEB_EXPORT_DIR.is_dir():
    app.mount("/play", StaticFiles(directory=_WEB_EXPORT_DIR, html=True), name="web_export")


@app.get("/")
async def root() -> dict:
    """Simple root route for sanity checks."""
    web_available = _WEB_EXPORT_DIR.is_dir()
    return {
        "service": "casuya-social-news",
        "docs": "/docs",
        "play": "/play" if web_available else None,
    }


_OPERATOR_HTML = Path(__file__).resolve().parent / "static" / "operator.html"


@app.get("/operator", include_in_schema=False)
async def operator_dashboard() -> Response:
    """Serve the operator console (JWT-authenticated in the browser)."""
    return HTMLResponse(_OPERATOR_HTML.read_text(encoding="utf-8"))


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus scrape endpoint (no API key — scoped to the scrape target)."""
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
