"""Script generation and synthesis endpoints (MVP).

POST /api/v1/scripts/generate      — news → script
POST /api/v1/scripts/generate-audio — script → audio files
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.errors import InvalidInputError, ScriptTimeoutError, TTSProviderError
from cache.redis_client import cache
from config.logging_config import get_logger
from config.settings import get_settings
from database.engine import SessionLocal
from database.models import NewsArticle, Script
from monitoring.metrics import SCRIPTS_GENERATED, TTS_REQUESTS
from nlp.contextualizer import contextualize
from security.api_key_auth import verify_api_key
from storage.audio_store import publish_audio
from voice.tts_provider import get_provider

_logger = get_logger("api.scripts")
_settings = get_settings()

router = APIRouter(dependencies=[Depends(verify_api_key)])


async def _generate_with_timeout(payload: NewsInput) -> dict:
    """Run script generation under a hard timeout (raises E1003 on breach)."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(contextualize, payload.model_dump(), direction=payload.direction),
            timeout=_settings.script_generation_timeout_seconds,
        )
    except TimeoutError as exc:
        _logger.error("script_generation_timeout", url=payload.url)
        raise ScriptTimeoutError(
            f"Script generation exceeded {_settings.script_generation_timeout_seconds}s"
        ) from exc


class NewsInput(BaseModel):
    """News article payload the contextualizer turns into a script."""

    headline: str = Field(..., min_length=3, max_length=512)
    source: str = Field(..., min_length=2, max_length=128)
    url: str = Field(..., min_length=5, max_length=1024)
    published_at: datetime | None = None
    direction: str = Field("utulivu", pattern="^(msisimko|furaha|wasiwasi|utulivu)$")


class GenerateResponse(BaseModel):
    script: dict


class AudioLineResponse(BaseModel):
    index: int
    character_id: str
    audio_url: str


class GenerateAudioResponse(BaseModel):
    script_id: str
    lines: list[AudioLineResponse]


@router.post("/generate", response_model=GenerateResponse)
async def generate_script(payload: NewsInput) -> GenerateResponse:
    """Convert a news item into a dramatic script (cached by URL)."""
    cache_key = f"script:{payload.url}"
    cached = await cache.get(cache_key)
    if cached:
        return GenerateResponse(script=cached)

    script = await _generate_with_timeout(payload)
    SCRIPTS_GENERATED.labels(direction=payload.direction).inc()
    await cache.set(cache_key, script)

    # Persist article + script (best-effort; pipeline must not fail on DB hiccups).
    try:
        async with SessionLocal() as session:
            article = NewsArticle(
                headline=payload.headline,
                source=payload.source,
                url=payload.url,
                published_at=payload.published_at or datetime.now(UTC),
                raw_content=payload.headline,
            )
            session.add(article)
            await session.flush()
            session.add(
                Script(
                    id=script["script_id"],
                    news_article_id=article.id,
                    full_json=script,
                )
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        _logger.warning("db_persist_failed", error=str(exc))

    return GenerateResponse(script=script)


@router.post("/generate-audio", response_model=GenerateAudioResponse)
async def generate_audio(payload: dict) -> GenerateAudioResponse:
    """Synthesize audio for every line of an already-generated script."""
    script_id = payload.get("script_id")
    script = payload.get("script")

    if script is None:
        cache_key = f"script:{script_id}" if script_id else None
        script = await cache.get(cache_key) if cache_key else None
    if script is None:
        raise InvalidInputError("script or script_id not provided")

    provider = get_provider()
    lines = script.get("lines", [])
    voice_map = {c["id"]: c["voice_id"] for c in script.get("characters", [])}

    results: list[AudioLineResponse] = []
    out_dir = _settings.storage_dir / script["script_id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    for line in lines:
        line_index = int(line["index"])
        out_path = out_dir / f"{line_index:02d}.wav"
        try:
            await provider.synthesize(
                text=line["text"],
                voice_id=voice_map.get(line["character_id"], "default"),
                out_path=out_path,
            )
            TTS_REQUESTS.labels(status="ok").inc()
            line["audio_url"] = publish_audio(out_path, script["script_id"])
            results.append(
                AudioLineResponse(
                    index=line_index,
                    character_id=line["character_id"],
                    audio_url=line["audio_url"],
                )
            )
        except Exception as exc:  # noqa: BLE001
            TTS_REQUESTS.labels(status="error").inc()
            _logger.error("tts_line_failed", index=line_index, error=str(exc))
            raise TTSProviderError(f"TTS synthesis failed for line {line_index}") from exc

    return GenerateAudioResponse(script_id=script["script_id"], lines=results)
