"""TTS provider guarded by a circuit breaker (README monitoring spec).

Wraps the configured provider; when the underlying voice API is failing
consistently, requests fast-fail with CircuitOpenError instead of hammering
a dead upstream. The provider factory returns the guarded proxy.
"""

from __future__ import annotations

from pathlib import Path

from config.logging_config import get_logger
from monitoring.circuit_breaker import CircuitBreaker, CircuitOpenError, run_with_breaker
from voice.tts_provider import TTSProvider

_logger = get_logger("voice.breaker")

_CIRCUIT = CircuitBreaker()


class BreakerTTSProxy(TTSProvider):
    """Pass-through that routes calls through the shared circuit breaker."""

    name = "breaker"

    def __init__(self, provider: TTSProvider) -> None:
        self._provider = provider
        self.name = provider.name

    @property
    def wrapped_name(self) -> str:
        return self._provider.name

    async def synthesize(
        self, text: str, voice_id: str, out_path: Path, *, quality: str = "high"
    ) -> Path:
        async def call() -> Path:
            return await self._provider.synthesize(text, voice_id, out_path, quality=quality)

        try:
            return await run_with_breaker(_CIRCUIT, call())
        except CircuitOpenError:
            _logger.error("tts_circuit_open", state=_CIRCUIT.state)
            raise
        except Exception as exc:  # noqa: BLE001 - logged by breaker, surfaced
            _logger.error("tts_breaker_failed", error=str(exc))
            raise

    async def health_check(self) -> bool:
        """Provider is healthy only if the circuit allows calls."""
        return _CIRCUIT.allow_request() and await self._provider.health_check()

    def circuit_snapshot(self) -> dict:
        return _CIRCUIT.snapshot()


def get_breaker_circuit() -> CircuitBreaker:
    """Access the shared breaker (for health routes / tests)."""
    return _CIRCUIT
