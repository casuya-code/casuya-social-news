"""Casuya Social News server entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.handlers import register_exception_handlers
from api.routes.v1.router import api_v1_router
from config.logging_config import setup_logging
from config.settings import get_settings
from middleware.request_id import RequestIDMiddleware

setup_logging()

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Ensure storage directory exists for audio assets.
    _settings.storage_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Casuya Social News",
    version="0.1.0",
    description="Real-time Swahili social news drama engine (server).",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RequestIDMiddleware)

# Serve synthesized audio from local storage.
os.makedirs(_settings.storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=_settings.storage_dir), name="storage")

app.include_router(api_v1_router)


@app.get("/")
async def root() -> dict:
    """Simple root route for sanity checks."""
    return {"service": "casuya-social-news", "docs": "/docs"}
