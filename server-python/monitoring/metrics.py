"""Prometheus metrics registry and exposure (README: monitoring/metrics.py).

Central registry of gauges/counters/histograms, a pure-ASGI middleware that
records every request, and the application-level counters instrumented by the
rest of the server (scheduler, economy, ingestor, websockets).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# --------------------------------------------------------------------------
# HTTP instrumentation
# --------------------------------------------------------------------------

HTTP_REQUESTS = Counter(
    "casuya_http_requests_total",
    "HTTP requests served, by method and path template.",
    labelnames=("method", "path", "status"),
)

HTTP_DURATION = Histogram(
    "casuya_http_request_duration_seconds",
    "Request handling duration in seconds.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# --------------------------------------------------------------------------
# Realtime (websocket) instrumentation
# --------------------------------------------------------------------------

WS_CONNECTIONS = Gauge(
    "casuya_websocket_connections",
    "Currently connected websocket clients.",
)
WS_MESSAGES_SENT = Counter(
    "casuya_websocket_messages_sent_total",
    "Websocket messages broadcast to clients.",
    labelnames=("message_type",),
)

# --------------------------------------------------------------------------
# Application-level instrumentation
# --------------------------------------------------------------------------

SCRIPTS_GENERATED = Counter(
    "casuya_scripts_generated_total",
    "Dramatic scripts produced, by direction.",
    labelnames=("direction",),
)

NEWS_INGESTED = Counter(
    "casuya_news_ingested_total",
    "News articles successfully ingested.",
)

VOTES_RECORDED = Counter(
    "casuya_votes_recorded_total",
    "Community votes recorded, by direction.",
    labelnames=("direction",),
)

TTS_REQUESTS = Counter(
    "casuya_tts_requests_total",
    "TTS synthesis attempts, by outcome.",
    labelnames=("status",),
)

SCHEDULER_CYCLES = Counter(
    "casuya_scheduler_cycles_total",
    "Background scheduler ingest cycles completed.",
)
SCHEDULER_ERRORS = Counter(
    "casuya_scheduler_errors_total",
    "Background scheduler cycles that failed.",
)
SCHEDULER_RUNNING = Gauge(
    "casuya_scheduler_running",
    "1 when the scheduler loop is running, 0 otherwise.",
)
SCHEDULER_LAST_DURATION = Gauge(
    "casuya_scheduler_last_cycle_duration_seconds",
    "Duration of the most recent scheduler cycle.",
)

# --------------------------------------------------------------------------
# Middleware + export
# --------------------------------------------------------------------------


def _path_template(path: str) -> str:
    """Collapse dynamic path segments so label cardinality stays bounded."""
    return "/".join(
        "{id}" if (_is_uuid(segment) or segment.isdigit()) else segment
        for segment in path.strip("/").split("/")
    )


def _is_uuid(value: str) -> bool:
    return len(value) == 32 and all(c in "0123456789abcdef" for c in value)


def render_metrics() -> tuple[str, str]:
    """Return (body, content_type) for a Prometheus scrape."""
    return generate_latest().decode("utf-8"), CONTENT_TYPE_LATEST


class MetricsMiddleware:
    """Pure-ASGI middleware recording request count and duration."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[Any]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = _path_template(scope.get("path", ""))

        status = {"code": 500}
        started = time.perf_counter()

        async def wrapped_send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, wrapped_send)

        elapsed = time.perf_counter() - started
        HTTP_DURATION.labels(method, path).observe(elapsed)
        HTTP_REQUESTS.labels(method, path, status["code"]).inc()
