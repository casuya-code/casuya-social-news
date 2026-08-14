"""Tests for the Prometheus metrics middleware and registry."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from monitoring.metrics import (
    HTTP_DURATION,
    HTTP_REQUESTS,
    SCRIPTS_GENERATED,
    VOTES_RECORDED,
    MetricsMiddleware,
    _path_template,
    render_metrics,
)


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/economy/stats/{script_id}")
    async def stats(script_id: str):
        return {"script_id": script_id}

    @app.get("/health")
    async def health():
        return {"ok": True}

    app.add_middleware(MetricsMiddleware)
    return app


def test_path_template_collapses_ids():
    assert (
        _path_template("/api/v1/economy/stats/abc123def456abc123def456abc123de")
        == "api/v1/economy/stats/{id}"
    )
    assert _path_template("/api/v1/news/42") == "api/v1/news/{id}"
    assert _path_template("/") == ""


def test_metrics_middleware_records_requests():
    client = TestClient(_build_app())
    client.get("/health")
    client.get("/api/v1/economy/stats/abc123def456abc123def456abc123de")

    rendered = render_metrics()[0]
    assert "casuya_http_requests_total" in rendered
    assert 'method="GET",path="health",status="200"' in rendered
    # dynamic path segments are collapsed, so cardinality stays bounded
    assert 'path="api/v1/economy/stats/{id}"' in rendered
    assert "casuya_http_request_duration_seconds" in rendered


def test_metrics_middleware_tracks_status_codes():
    client = TestClient(_build_app())
    client.get("/does-not-exist")
    rendered = render_metrics()[0]
    assert 'path="does-not-exist",status="404"' in rendered


def test_application_counters_are_exported():
    from monitoring.metrics import NEWS_INGESTED, TTS_REQUESTS

    SCRIPTS_GENERATED.labels(direction="furaha").inc()
    VOTES_RECORDED.labels(direction="msisimko").inc()
    NEWS_INGESTED.inc()
    TTS_REQUESTS.labels(status="ok").inc()
    rendered = render_metrics()[0]
    # counters are process-global, so other tests may have incremented them —
    # assert the label series exists, not an exact cumulative value
    assert 'casuya_scripts_generated_total{direction="furaha"}' in rendered
    assert 'casuya_votes_recorded_total{direction="msisimko"}' in rendered
    assert "casuya_news_ingested_total" in rendered
    assert 'casuya_tts_requests_total{status="ok"}' in rendered


def test_http_counters_match_histogram():
    # both derive from the same underlying request stream
    labels = ("GET", "health", "200")
    before = HTTP_REQUESTS.labels(*labels)._value.get()
    HTTP_DURATION.labels("GET", "health").observe(0.1)
    assert HTTP_DURATION.labels("GET", "health")._sum.get() >= 0.1
    HTTP_REQUESTS.labels(*labels).inc()
    after = HTTP_REQUESTS.labels(*labels)._value.get()
    assert after == before + 1
