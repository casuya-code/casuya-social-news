"""Tests for circuit breaker provider integration and error envelope fallbacks."""

import pytest

from monitoring.circuit_breaker import CircuitBreaker, CircuitOpenError, run_with_breaker


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


async def _async_provider_success() -> dict:
    return {"status": "ok", "audio_url": "/static/audio/test.wav"}


async def _async_provider_timeout() -> dict:
    raise TimeoutError("TTS Provider unreachable")


@pytest.mark.asyncio
async def test_circuit_breaker_fallback_lifecycle():
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=30.0, clock=clock)

    # 1. Closed state: calls pass through successfully
    res = await run_with_breaker(breaker, _async_provider_success())
    assert res["status"] == "ok"
    assert breaker.state == "closed"

    # 2. First failure: registers but stays closed
    with pytest.raises(TimeoutError):
        await run_with_breaker(breaker, _async_provider_timeout())
    assert breaker.state == "closed"
    assert breaker.snapshot()["consecutive_failures"] == 1

    # 3. Second failure: exceeds threshold, trips circuit to OPEN
    with pytest.raises(TimeoutError):
        await run_with_breaker(breaker, _async_provider_timeout())
    assert breaker.state == "open"
    assert breaker.allow_request() is False

    # 4. In OPEN state: requests fast-fail with CircuitOpenError without calling provider
    with pytest.raises(CircuitOpenError):
        await run_with_breaker(breaker, _async_provider_success())

    # 5. Advance clock past recovery window -> HALF_OPEN
    clock.advance(35.0)
    assert breaker.state == "half_open"
    assert breaker.allow_request() is True

    # 6. Success during HALF_OPEN closes circuit
    res = await run_with_breaker(breaker, _async_provider_success())
    assert res["status"] == "ok"
    assert breaker.state == "closed"
    assert breaker.snapshot()["consecutive_failures"] == 0
