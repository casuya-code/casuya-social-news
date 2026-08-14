"""Tests for the background story scheduler."""

import pytest

from task_queue.scheduler import IngestScheduler


@pytest.mark.asyncio
async def test_scheduler_runs_ingest_cycles(monkeypatch):
    calls = {"count": 0}

    async def fake_ingest():
        calls["count"] += 1
        return [{"script_id": f"s{calls['count']}"}]

    monkeypatch.setattr("task_queue.scheduler.ingest_and_generate", fake_ingest)
    scheduler = IngestScheduler(interval_seconds=0.05)
    await scheduler.start()
    assert scheduler.running is True

    for _ in range(50):
        if calls["count"] >= 2:
            break
        await asyncio_sleep(0.02)

    assert calls["count"] >= 2
    assert scheduler.cycles_completed >= 2
    assert scheduler.stories_generated >= 2
    await scheduler.stop()
    assert scheduler.running is False


@pytest.mark.asyncio
async def test_scheduler_survives_errors(monkeypatch):
    async def failing_ingest():
        raise RuntimeError("boom")

    async def good_ingest():
        return [{"script_id": "ok"}]

    state = {"failing": True}
    monkeypatch.setattr(
        "task_queue.scheduler.ingest_and_generate",
        lambda: failing_ingest() if state["failing"] else good_ingest(),
    )
    scheduler = IngestScheduler(interval_seconds=0.05)
    await scheduler.start()

    for _ in range(50):
        if scheduler.last_error is not None:
            break
        await asyncio_sleep(0.02)
    assert scheduler.last_error == "boom"
    assert scheduler.cycles_completed == 0

    state["failing"] = False
    for _ in range(100):
        if scheduler.cycles_completed >= 1:
            break
        await asyncio_sleep(0.02)
    assert scheduler.cycles_completed >= 1  # recovered after the failure
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_start_is_idempotent(monkeypatch):
    async def fake_ingest():
        return []

    monkeypatch.setattr("task_queue.scheduler.ingest_and_generate", fake_ingest)
    scheduler = IngestScheduler(interval_seconds=0.05)
    await scheduler.start()
    first = scheduler._task
    await scheduler.start()  # second start must not spawn a second loop
    assert scheduler._task is first
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_stop_cleanly(monkeypatch):
    async def fake_ingest():
        return []

    monkeypatch.setattr("task_queue.scheduler.ingest_and_generate", fake_ingest)
    scheduler = IngestScheduler(interval_seconds=0.05)
    await scheduler.start()
    await scheduler.stop()
    assert scheduler.running is False
    assert scheduler.snapshot()["running"] is False


@pytest.mark.asyncio
async def test_scheduler_snapshot_reports_state():
    scheduler = IngestScheduler(interval_seconds=60)
    snap = scheduler.snapshot()
    assert snap["running"] is False
    assert snap["interval_seconds"] == 60
    assert snap["cycles_completed"] == 0


@pytest.mark.asyncio
async def test_scheduler_runs_retention_on_frequency(monkeypatch):
    calls = {"ingest": 0, "retention": 0}

    async def fake_ingest():
        calls["ingest"] += 1
        return [{"script_id": "s"}]

    async def fake_retention(self):
        calls["retention"] += 1

    monkeypatch.setattr("task_queue.scheduler.ingest_and_generate", fake_ingest)
    monkeypatch.setattr("task_queue.scheduler.IngestScheduler._run_retention", fake_retention)
    scheduler = IngestScheduler(interval_seconds=0.05, retention_cycle_frequency=2)
    await scheduler.start()

    for _ in range(100):
        if calls["retention"] >= 1:
            break
        await asyncio_sleep(0.02)

    assert calls["ingest"] >= 2
    assert calls["retention"] >= 1
    assert scheduler.snapshot()["retention_enabled"] is True
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_retention_can_be_disabled(monkeypatch):
    calls = {"ingest": 0, "retention": 0}

    async def fake_ingest():
        calls["ingest"] += 1
        return []

    async def fake_retention(self):
        calls["retention"] += 1

    monkeypatch.setattr("task_queue.scheduler.ingest_and_generate", fake_ingest)
    monkeypatch.setattr("task_queue.scheduler.IngestScheduler._run_retention", fake_retention)
    scheduler = IngestScheduler(
        interval_seconds=0.05, retention_cycle_frequency=1, retention_enabled=False
    )
    await scheduler.start()

    for _ in range(50):
        if calls["ingest"] >= 3:
            break
        await asyncio_sleep(0.02)

    assert calls["retention"] == 0
    assert scheduler.snapshot()["retention_enabled"] is False
    await scheduler.stop()


async def asyncio_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
