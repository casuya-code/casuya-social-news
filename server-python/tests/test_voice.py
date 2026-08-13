"""Tests for the mock TTS provider."""

import pytest

from voice.mock_provider import MockProvider


@pytest.mark.asyncio
async def test_mock_provider_writes_wav(tmp_path):
    provider = MockProvider()
    out = tmp_path / "line.wav"
    result = await provider.synthesize("Habari za leo", "mock_bibi", out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 44  # WAV header is 44 bytes


@pytest.mark.asyncio
async def test_mock_provider_health():
    provider = MockProvider()
    assert await provider.health_check() is True
