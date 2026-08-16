"""ElevenLabs TTS client (optional premium provider).

Enable with `TTS_PROVIDER=elevenlabs` and `ELEVENLABS_API_KEY`.
Budget-capped via `ELEVENLABS_MONTHLY_BUDGET_USD`.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from api.errors import TTSQuotaError, TTSWriteError
from config.logging_config import get_logger
from config.settings import get_settings
from voice.tts_provider import TTSProvider

_settings = get_settings()
_logger = get_logger("voice.elevenlabs")

_ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
_MODEL_ID = "eleven_multilingual_v2"
_PRICE_PER_1M_CHARS_USD = 100.0

# Process-local char budget tracker for the monthly cap (README cost controls).
_chars_synthesized_this_month = 0


class ElevenLabsProvider(TTSProvider):
    """Synthesizes Swahili audio via ElevenLabs' multilingual v2 model."""

    name = "elevenlabs"

    def __init__(self) -> None:
        self._api_key = _settings.elevenlabs_api_key
        if not self._api_key:
            _logger.warning("elevenlabs_api_key not set; provider will fail health checks")

    @property
    def _monthly_char_budget(self) -> int:
        """Max chars for the month, derived from the USD budget cap."""
        return int(_settings.elevenlabs_monthly_budget_usd * 1_000_000 / _PRICE_PER_1M_CHARS_USD)

    async def synthesize(
        self, text: str, voice_id: str, out_path: Path, *, quality: str = "high"
    ) -> Path:
        global _chars_synthesized_this_month
        if not self._api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not configured")
        if (
            _settings.elevenlabs_monthly_budget_usd > 0
            and _chars_synthesized_this_month >= self._monthly_char_budget
        ):
            raise TTSQuotaError("ElevenLabs monthly budget exhausted")

        url = f"{_ELEVENLABS_URL}/{voice_id}"
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        model_id = _MODEL_ID if quality == "high" else "eleven_turbo_v2"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5 if quality == "high" else 0.3,
                "similarity_boost": 0.75 if quality == "high" else 0.5,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        _chars_synthesized_this_month += len(text)

        try:
            out_path.write_bytes(response.content)
        except OSError as exc:  # noqa: BLE001 - disk/path failures are E2003
            raise TTSWriteError(f"audio write failed: {exc}") from exc
        return out_path

    async def health_check(self) -> bool:
        return bool(self._api_key)

    @property
    def estimated_monthly_cost_usd(self) -> float:
        """Rough cost projection based on current budget cap."""
        return round(
            _settings.elevenlabs_monthly_budget_usd, 2
        )
