"""Tests for the rate limiter middleware."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from middleware.rate_limiter import (
    GENERAL_LIMIT,
    VOICE_LIMIT,
    RateLimiterMiddleware,
    _SlidingWindow,
    client_key,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_sliding_window_counts_within_window():
    clock = FakeClock()
    window = _SlidingWindow(clock=clock)
    window.hit("general", "1.2.3.4")
    window.hit("general", "1.2.3.4")
    assert window.count("general", "1.2.3.4") == 2
    clock.advance(61.0)
    assert window.count("general", "1.2.3.4") == 0  # expired


def test_sliding_window_separates_buckets_and_clients():
    clock = FakeClock()
    window = _SlidingWindow(clock=clock)
    window.hit("general", "a")
    window.hit("voice", "a")
    assert window.count("general", "a") == 1
    assert window.count("voice", "a") == 1
    assert window.count("general", "b") == 0


def test_client_key_prefers_forwarded_header():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-forwarded-for", b"9.9.9.9, 8.8.8.8")],
        "client": ("1.2.3.4", 1234),
        "query_string": b"",
        "asgi": {"version": "3.0"},
    }
    request = Request(scope)
    assert client_key(request) == "9.9.9.9"


def _build_app(window, *, voice: bool = False):
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.get("/api/v1/scripts/generate-audio")
    async def voice_route():
        return {"ok": True}

    app.add_middleware(RateLimiterMiddleware, window=window)
    return app


def test_rate_limits_general_bucket():
    clock = FakeClock()
    window = _SlidingWindow(clock=clock)
    client = TestClient(_build_app(window))
    for _ in range(GENERAL_LIMIT):
        assert client.get("/health").status_code == 200
    limited = client.get("/health")
    assert limited.status_code == 429
    assert limited.json()["error_code"] == "E4003"


def test_rate_limits_voice_bucket_stricter():
    clock = FakeClock()
    window = _SlidingWindow(clock=clock)
    client = TestClient(_build_app(window))
    for _ in range(VOICE_LIMIT):
        assert client.get("/api/v1/scripts/generate-audio").status_code == 200
    limited = client.get("/api/v1/scripts/generate-audio")
    assert limited.status_code == 429
    # general bucket untouched by voice calls
    assert client.get("/health").status_code == 200


def test_rate_limit_expires_with_window():
    clock = FakeClock()
    window = _SlidingWindow(clock=clock)
    client = TestClient(_build_app(window))
    for _ in range(GENERAL_LIMIT):
        client.get("/health")
    assert client.get("/health").status_code == 429
    clock.advance(61.0)
    assert client.get("/health").status_code == 200
