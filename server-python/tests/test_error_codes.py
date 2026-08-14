"""Tests for the remaining error codes (E1002, E2002, E2003, E5001, E5002)."""

import asyncio
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.errors import (
    EmotionTaggingError,
    NewsRateLimitedError,
    NewsSourceError,
    TTSQuotaError,
    TTSWriteError,
)
from api.handlers import register_exception_handlers


def test_error_codes_are_implemented():
    assert EmotionTaggingError.error_code == "E1002"
    assert TTSQuotaError.error_code == "E2002"
    assert TTSWriteError.error_code == "E2003"
    assert NewsSourceError.error_code == "E5001"
    assert NewsRateLimitedError.error_code == "E5002"


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/boom/emotion")
    async def emotion():
        raise EmotionTaggingError("unknown emotion tag")

    @app.get("/boom/quota")
    async def quota():
        raise TTSQuotaError("budget exhausted")

    @app.get("/boom/write")
    async def write():
        raise TTSWriteError("audio write failed")

    @app.get("/boom/source")
    async def source():
        raise NewsSourceError("news source unavailable")

    @app.get("/boom/rate")
    async def rate():
        raise NewsRateLimitedError("news source rate limited")

    register_exception_handlers(app)
    return app


def test_emotion_error_envelope():
    client = TestClient(_build_app())
    r = client.get("/boom/emotion")
    assert r.status_code == 500
    assert r.json()["error_code"] == "E1002"


def test_quota_error_envelope():
    client = TestClient(_build_app())
    r = client.get("/boom/quota")
    assert r.status_code == 429
    assert r.json()["error_code"] == "E2002"


def test_write_error_envelope():
    client = TestClient(_build_app())
    r = client.get("/boom/write")
    assert r.status_code == 500
    assert r.json()["error_code"] == "E2003"


def test_news_source_error_envelope():
    client = TestClient(_build_app())
    r = client.get("/boom/source")
    assert r.status_code == 503
    assert r.json()["error_code"] == "E5001"


def test_news_rate_limited_envelope():
    client = TestClient(_build_app())
    r = client.get("/boom/rate")
    assert r.status_code == 429
    assert r.json()["error_code"] == "E5002"


def test_emotion_tagger_raises_e1002_when_registry_mismatch(monkeypatch, tmp_path):
    """If the shared registry ever omits a tag the code emits, fail loudly."""
    from nlp import emotion_tagger

    # Point the tagger at an empty registry so every emitted tag is "missing".
    empty = tmp_path / "emotion_tags.json"
    empty.write_text('{"examples": []}', encoding="utf-8")
    monkeypatch.setattr(
        emotion_tagger,
        "_load_registry_tags",
        lambda: set(),
    )

    # Empty registry → no validation (offline-safe), so no error.
    assert emotion_tagger.tag_line(0) == "anashangaa"

    # A registry that is missing a tag the code emits must raise E1002.
    monkeypatch.setattr(emotion_tagger, "_load_registry_tags", lambda: {"anafikiria"})
    with pytest.raises(EmotionTaggingError):
        emotion_tagger.tag_line(0)


def test_mock_tts_raises_e2003_on_write_failure(monkeypatch):
    from voice.mock_provider import MockProvider

    provider = MockProvider()

    def boom_write(path, freq, duration):
        raise OSError("disk full")

    monkeypatch.setattr("voice.mock_provider._write_tone", boom_write)
    with pytest.raises(TTSWriteError):
        asyncio.run(provider.synthesize("habari", "mock_a", Path("x.wav")))


def test_news_client_raises_e5002_on_429():
    from scraper.news_api_client import NewsApiClient

    client = NewsApiClient()
    client._api_key = "dummy-key"  # force the real-API path

    class FakeResponse:
        status_code = 429

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "429", request=httpx.Request("GET", "http://x"), response=self
            )

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, params=None):
            return FakeResponse()

    monkeypatch_httpx = pytest.MonkeyPatch()
    monkeypatch_httpx.setattr("scraper.news_api_client.httpx.AsyncClient", FakeClient)

    async def run():
        with pytest.raises(NewsRateLimitedError):
            await client.fetch_latest(5)

    asyncio.run(run())
    monkeypatch_httpx.undo()


def test_news_client_raises_e5001_after_retries():
    from scraper.news_api_client import NewsApiClient as Cls

    client = Cls()
    client._api_key = "dummy-key"

    class FakeResponse:
        status_code = 500

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "500", request=httpx.Request("GET", "http://x"), response=self
            )

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url, params=None):
            return FakeResponse()

    monkeypatch_httpx = pytest.MonkeyPatch()
    monkeypatch_httpx.setattr("scraper.news_api_client.httpx.AsyncClient", FakeClient)
    monkeypatch_httpx.setattr("scraper.news_api_client._RETRY_DELAYS", (0, 0, 0))

    async def run():
        with pytest.raises(NewsSourceError):
            await client.fetch_latest(5)

    asyncio.run(run())
    monkeypatch_httpx.undo()


def test_ingest_degrades_to_mock_on_news_error(monkeypatch):
    """E5001/E5002 must not stall the pipeline: fall back to the mock feed."""
    from scraper import ingestor

    calls = {"real": 0, "mock": 0}

    async def boom_fetch(limit):
        calls["real"] += 1
        raise NewsSourceError("down")

    async def mock_fetch(limit):
        calls["mock"] += 1
        return [
            {
                "title": "Habari ya mtihani",
                "url": f"https://example.com/{uuid4().hex}",
                "source": {"name": "Mock"},
                "publishedAt": "2026-08-14T08:00:00Z",
            }
        ]

    class FakeReal:
        async def fetch_latest(self, limit):
            return await boom_fetch(limit)

    class FakeMock:
        async def fetch_latest(self, limit):
            return await mock_fetch(limit)

    monkeypatch.setattr(ingestor, "NewsApiClient", lambda: FakeReal())
    monkeypatch.setattr(ingestor, "MockFeed", lambda: FakeMock())

    async def run():
        fresh = await ingestor.ingest(limit=3)
        assert len(fresh) == 1
        assert fresh[0]["headline"] == "Habari ya mtihani"

    asyncio.run(run())
    assert calls["real"] == 1
    assert calls["mock"] == 1
