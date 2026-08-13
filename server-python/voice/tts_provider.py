"""TTS provider abstraction. Switch providers via the `TTS_PROVIDER` setting.

Providers: mock (default, offline) | google_cloud | elevenlabs
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from config.settings import get_settings

_settings = get_settings()


class TTSProvider(ABC):
    """Interface every voice provider implements."""

    name: str = "base"

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, out_path: Path) -> Path:
        """Synthesize text to audio, write it to out_path, return the path."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is available."""
        raise NotImplementedError


def get_provider() -> TTSProvider:
    """Factory returning the configured provider (cached at module level)."""
    provider_name = _settings.tts_provider
    if provider_name == "elevenlabs":
        from voice.elevenlabs_client import ElevenLabsProvider

        return ElevenLabsProvider()
    if provider_name == "google_cloud":
        from voice.google_cloud_client import GoogleCloudProvider

        return GoogleCloudProvider()
    from voice.mock_provider import MockProvider

    return MockProvider()
