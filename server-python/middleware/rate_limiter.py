"""Rate limiting middleware (README: 60 req/min per IP, 5 req/min voice).

Sliding-window counters kept in memory (Redis would share state across
replicas in production). Voice-generation routes get a stricter budget.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config.logging_config import get_logger

_logger = get_logger("middleware.rate_limiter")

GENERAL_LIMIT = 60  # requests per minute per IP
VOICE_LIMIT = 5  # voice-generation requests per minute per IP
_WINDOW = 60.0  # seconds

_VOICE_PATHS = ("/api/v1/scripts/generate-audio", "/api/v1/voice/")


class _SlidingWindow:
    """Minute-window counter keyed by (bucket, key)."""

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def count(self, bucket: str, key: str) -> int:
        """Return hits within the last window for bucket+key."""
        now = self._clock()
        with self._lock:
            timestamps = self._hits[(bucket, key)]
            timestamps[:] = [t for t in timestamps if now - t < _WINDOW]
            return len(timestamps)

    def hit(self, bucket: str, key: str) -> None:
        now = self._clock()
        with self._lock:
            self._hits[(bucket, key)].append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_rate_window = _SlidingWindow()


def client_key(request: Request) -> str:
    """Identify a client by real IP, falling back to the forwarded header."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Enforce per-IP request budgets per minute."""

    def __init__(self, app: Any, *, window: _SlidingWindow | None = None) -> None:
        super().__init__(app)
        self._window = window or _rate_window

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        key = client_key(request)
        path = request.url.path

        bucket = "voice" if any(path.startswith(p) for p in _VOICE_PATHS) else "general"
        limit = VOICE_LIMIT if bucket == "voice" else GENERAL_LIMIT

        if self._window.count(bucket, key) >= limit:
            _logger.warning("rate_limited", bucket=bucket, client=key)
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "E4003",
                    "message": "Rate limit exceeded",
                    "bucket": bucket,
                    "limit": limit,
                },
                headers={"Retry-After": str(int(_WINDOW))},
            )

        self._window.hit(bucket, key)
        return await call_next(request)
