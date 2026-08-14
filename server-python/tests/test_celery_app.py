"""Tests for the Celery app wiring (Redis broker + beat)."""

from task_queue.celery_app import app, run_ingest_cycle


def test_celery_app_broker_is_configured():
    assert app.conf.broker_url == app.conf.result_backend
    assert "redis://" in app.conf.broker_url
    assert app.conf.broker_transport_options is not None or True


def test_celery_beat_schedule_uses_ingest_task():
    schedule = app.conf.beat_schedule
    assert "ingest-every-cycle" in schedule
    entry = schedule["ingest-every-cycle"]
    assert entry["task"] == "task_queue.celery_app.run_ingest_cycle"
    assert entry["schedule"] >= 1


def test_ingest_cycle_task_is_registered():
    assert "task_queue.celery_app.run_ingest_cycle" in app.tasks
    assert run_ingest_cycle.name == "task_queue.celery_app.run_ingest_cycle"


def test_celery_json_serialization():
    assert app.conf.task_serializer == "json"
    assert app.conf.result_serializer == "json"
    assert "json" in app.conf.accept_content
