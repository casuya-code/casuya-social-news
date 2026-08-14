"""Google Cloud TTS client (default production provider).

Requires `TTS_PROVIDER=google_cloud` and either ADC (gcloud auth) or
`GOOGLE_APPLICATION_CREDENTIALS`. Falls back to an explicit error when the
client library or credentials are missing — never silently.
"""

from __future__ import annotations

from pathlib import Path

from api.errors import TTSWriteError
from config.logging_config import get_logger
from config.settings import get_settings
from voice.tts_provider import TTSProvider

_settings = get_settings()
_logger = get_logger("voice.google_cloud")


class GoogleCloudProvider(TTSProvider):
    """Wraps google-cloud-texttospeech for Swahili voices (sw-SW)."""

    name = "google_cloud"

    def __init__(self) -> None:
        self._client = None

    def _client_or_raise(self):
        if self._client is None:
            try:
                from google.cloud import texttospeech
            except ImportError as exc:  # pragma: no cover - depends on deps
                raise RuntimeError(
                    "google-cloud-texttospeech not installed. "
                    "Add it to requirements.txt or use TTS_PROVIDER=mock."
                ) from exc
            self._client = texttospeech.TextToSpeechClient()
        return self._client

    async def synthesize(self, text: str, voice_id: str, out_path: Path) -> Path:
        client = self._client_or_raise()
        synthesis_input = {"text": text}
        voice = {"language_code": "sw-SW", "name": voice_id}
        audio_config = {"audio_encoding": "MP3"}

        # Run in a thread; google-cloud client is blocking.
        import asyncio

        response = await asyncio.to_thread(
            client.synthesize_speech,
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        try:
            out_path.write_bytes(response.audio_content)
        except OSError as exc:  # noqa: BLE001 - disk/path failures are E2003
            raise TTSWriteError(f"audio write failed: {exc}") from exc
        return out_path

    async def health_check(self) -> bool:
        try:
            self._client_or_raise()
            return True
        except Exception:  # noqa: BLE001 - health check should not raise
            return False
