"""ElevenLabs TTS client (optional premium provider).

Enable with `TTS_PROVIDER=elevenlabs` and `ELEVENLABS_API_KEY`.
Budget-capped via `ELEVENLABS_MONTHLY_BUDGET_USD`.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from config.logging_config import get_logger
from config.settings import get_settings
from voice.tts_provider import TTSProvider

_settings = get_settings()
_logger = get_logger("voice.elevenlabs")

_ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
_MODEL_ID = "eleven_multilingual_v2"
_PRICE_PER_1M_CHARS_USD = 100.0


class ElevenLabsProvider(TTSProvider):
    """Synthesizes Swahili audio via ElevenLabs' multilingual v2 model."""

    name = "elevenlabs"

    def __init__(self) -> None:
        self._api_key = _settings.elevenlabs_api_key
        if not self._api_key:
            _logger.warning("elevenlabs_api_key not set; provider will fail health checks")

    async def synthesize(self, text: str, voice_id: str, out_path: Path) -> Path:
        if not self._api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not configured")

        url = f"{_ELEVENLABS_URL}/{voice_id}"
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": _MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        out_path.write_bytes(response.content)
        return out_path

    async def health_check(self) -> bool:
        return bool(self._api_key)

    @property
    def estimated_monthly_cost_usd(self, chars: int) -> float:
        """Rough cost projection for budgeting."""
        return round(chars / 1_000_000 * _PRICE_PER_1M_CHARS_USD, 2)
