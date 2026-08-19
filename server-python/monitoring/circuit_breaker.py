"""Circuit breaker for external providers (README reliability spec).

States:
  CLOSED   → calls pass through; count consecutive failures
  OPEN     → reject calls immediately (fast-fail) for `recovery_seconds`
  HALF_OPEN → allow one probe call; success closes, failure reopens

Defaults: open after 5 consecutive failures, half-open after 60s.
"""

from __future__ import annotations

import threading
import time


class CircuitOpenError(RuntimeError):
    """Raised when the breaker rejects a call because the circuit is open."""


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_seconds: float = 60.0,
        clock=time.monotonic,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_seconds = recovery_seconds
        self._clock = clock
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._state = "closed"
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Current state: closed | open | half_open."""
        with self._lock:
            if self._state == "open" and self._elapsed_since_open() >= self._recovery_seconds:
                self._state = "half_open"
            return self._state

    def _elapsed_since_open(self) -> float:
        return self._clock() - self._opened_at if self._opened_at is not None else 0.0

    def allow_request(self) -> bool:
        """Whether a call may proceed right now."""
        return self.state in ("closed", "half_open")

    def record_success(self) -> None:
        """A call succeeded: reset failures and close the circuit."""
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None
            self._state = "closed"

    def record_failure(self) -> None:
        """A call failed: maybe open the circuit."""
        with self._lock:
            self._consecutive_failures += 1
            if self._state == "half_open":
                self._open()
            elif self._consecutive_failures >= self._failure_threshold:
                self._open()

    def _open(self) -> None:
        self._state = "open"
        self._opened_at = self._clock()

    def reset(self) -> None:
        """Force the breaker back to a clean closed state (tests/admin)."""
        with self._lock:
            self._consecutive_failures = 0
            self._opened_at = None
            self._state = "closed"

    def snapshot(self) -> dict:
        """Machine-readable status for health checks."""
        state = self.state
        return {
            "state": state,
            "consecutive_failures": self._consecutive_failures,
            "failure_threshold": self._failure_threshold,
            "recovery_seconds": self._recovery_seconds,
            "opened_at": self._opened_at,
        }


async def run_with_breaker(breaker: CircuitBreaker, fn):
    """Execute `fn` under the breaker's rules.

    Fast-fails with CircuitOpenError when open; records success/failure
    otherwise. `fn` may be sync or async.
    """
    if not breaker.allow_request():
        if hasattr(fn, "close") and callable(fn.close):
            fn.close()
        raise CircuitOpenError(f"circuit is {breaker.state}")
    try:
        result = fn() if not hasattr(fn, "__await__") else await fn
        breaker.record_success()
        return result
    except Exception:
        breaker.record_failure()
        raise
