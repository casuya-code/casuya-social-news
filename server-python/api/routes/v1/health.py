"""Health check endpoint. Returns service + dependency status."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.errors import DatabaseError
from cache.redis_client import cache
from config.logging_config import get_logger
from config.settings import get_settings
from database.engine import SessionLocal
from security.api_key_auth import verify_api_key
from voice.tts_provider import get_provider

_logger = get_logger("api.health")
_settings = get_settings()

router = APIRouter()


@router.get("/health")
async def health_check(_: str = Depends(verify_api_key)) -> dict:
    """Liveness + readiness probe: DB, cache, and TTS provider."""
    status = {"status": "ok", "dependencies": {}}

    # Database
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        status["dependencies"]["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        _logger.error("db_health_failed", error=str(exc))
        status["dependencies"]["database"] = "down"
        raise DatabaseError("Database unreachable") from exc

    # Cache
    try:
        await cache.exists("__health__")
        status["dependencies"]["cache"] = "ok"
    except Exception as exc:  # noqa: BLE001
        _logger.error("cache_health_failed", error=str(exc))
        status["dependencies"]["cache"] = "down"

    # TTS provider
    try:
        provider = get_provider()
        healthy = await provider.health_check()
        status["dependencies"]["tts"] = provider.name if healthy else "down"
    except Exception as exc:  # noqa: BLE001
        _logger.error("tts_health_failed", error=str(exc))
        status["dependencies"]["tts"] = "down"

    status["app_env"] = _settings.app_env
    return status
