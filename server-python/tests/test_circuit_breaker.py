"""Tests for the circuit breaker (README monitoring spec)."""

import pytest

from monitoring.circuit_breaker import CircuitBreaker, CircuitOpenError, run_with_breaker


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_starts_closed_and_allows_requests():
    breaker = CircuitBreaker()
    assert breaker.state == "closed"
    assert breaker.allow_request() is True


def test_opens_after_threshold_failures():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=3, recovery_seconds=60.0, clock=clock)
    for _ in range(3):
        breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.allow_request() is False


def test_success_resets_failure_count():
    breaker = CircuitBreaker(failure_threshold=3)
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.snapshot()["consecutive_failures"] == 0


def test_half_open_after_recovery_seconds():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60.0, clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == "open"
    clock.advance(61.0)
    assert breaker.state == "half_open"
    assert breaker.allow_request() is True


def test_success_in_half_open_closes():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60.0, clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    clock.advance(61.0)
    assert breaker.state == "half_open"
    breaker.record_success()
    assert breaker.state == "closed"


def test_failure_in_half_open_reopens():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60.0, clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    clock.advance(61.0)
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.allow_request() is False


@pytest.mark.asyncio
async def test_run_with_breaker_fast_fails_when_open():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=60.0, clock=clock)
    breaker.record_failure()  # open after 1 failure
    with pytest.raises(CircuitOpenError):
        await run_with_breaker(breaker, _async_ok())


@pytest.mark.asyncio
async def test_run_with_breaker_records_success():
    breaker = CircuitBreaker(failure_threshold=3)
    result = await run_with_breaker(breaker, _async_ok())
    assert result == "ok"
    assert breaker.state == "closed"
    assert breaker.snapshot()["consecutive_failures"] == 0


@pytest.mark.asyncio
async def test_run_with_breaker_records_failure():
    breaker = CircuitBreaker(failure_threshold=2)
    with pytest.raises(RuntimeError):
        await run_with_breaker(breaker, _async_bad())
    assert breaker.state == "closed"  # 1 < threshold
    assert breaker.snapshot()["consecutive_failures"] == 1


@pytest.mark.asyncio
async def test_run_with_breaker_supports_sync_callables():
    breaker = CircuitBreaker()
    result = await run_with_breaker(breaker, lambda: "sync-ok")
    assert result == "sync-ok"


def _async_ok():
    async def ok() -> str:
        return "ok"

    return ok()


def _async_bad():
    async def bad() -> str:
        raise RuntimeError("boom")

    return bad()
