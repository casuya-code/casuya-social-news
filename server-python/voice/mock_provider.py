"""Mock TTS provider — writes a minimal valid WAV so the MVP works offline."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from api.errors import TTSWriteError
from config.settings import get_settings
from voice.tts_provider import TTSProvider

_settings = get_settings()

SAMPLE_RATE = 8000
DURATION_PER_CHAR = 0.06  # seconds of tone per character


class MockProvider(TTSProvider):
    """Generates a beep-based WAV instead of real speech.

    Purpose: let the full pipeline (generate → route → download) run with
    zero API keys. Replace by setting TTS_PROVIDER=google_cloud.
    """

    name = "mock"

    async def synthesize(self, text: str, voice_id: str, out_path: Path) -> Path:
        duration = max(0.5, len(text) * DURATION_PER_CHAR)
        freq = _frequency_for(voice_id)
        try:
            _write_tone(out_path, freq, duration)
        except OSError as exc:  # noqa: BLE001 - disk/path failures are E2003
            raise TTSWriteError(f"audio write failed: {exc}") from exc
        return out_path

    async def health_check(self) -> bool:
        return True


def _frequency_for(voice_id: str) -> float:
    """Deterministic pitch per voice so characters sound distinct."""
    return 200.0 + (abs(hash(voice_id)) % 8) * 40.0


def _write_tone(path: Path, freq: float, duration: float) -> None:
    """Write a simple sine-wave WAV file."""
    n_frames = int(SAMPLE_RATE * duration)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for i in range(n_frames):
            sample = int(12000 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
            frames += struct.pack("<h", sample)
        wf.writeframes(bytes(frames))
