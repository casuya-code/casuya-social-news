"""Tests for world clock and meteorological feed (Features #14, #30)."""

from datetime import UTC, datetime

import pytest

from nlp.memory import clamp
from weather_sync.geo_clock import time_of_day, utc_offset_hours
from weather_sync.meteorological_feed import (
    CONDITION_MOOD_OFFSET,
    MockWeatherFeed,
    OpenWeatherFeed,
    get_weather_feed,
    mood_offset,
)


def test_utc_offset_for_known_cities():
    assert utc_offset_hours("Dar es Salaam") == 3
    assert utc_offset_hours("Nairobi") == 3
    assert utc_offset_hours("Accra") == 0
    assert utc_offset_hours("unknown-town") == 0


def test_time_of_day_buckets():
    morning = datetime(2026, 8, 13, 7, 0, tzinfo=UTC)
    noon = datetime(2026, 8, 13, 13, 0, tzinfo=UTC)
    night = datetime(2026, 8, 13, 21, 0, tzinfo=UTC)
    assert time_of_day("Dar es Salaam", now=morning) == "asubuhi"
    assert time_of_day("Dar es Salaam", now=noon) == "mchana"
    assert time_of_day("Dar es Salaam", now=night) == "usiku"


def test_time_of_day_respects_location_offset():
    # 23:00 UTC is still "usiku" in London (UTC) but 02:00 next day in Dar (+3).
    late = datetime(2026, 8, 13, 23, 0, tzinfo=UTC)
    assert time_of_day("London", now=late) == "usiku"
    assert time_of_day("Dar es Salaam", now=late) == "usiku"
    # 02:00 UTC -> 05:00 in Dar (+3) = asubuhi.
    early = datetime(2026, 8, 13, 2, 0, tzinfo=UTC)
    assert time_of_day("Dar es Salaam", now=early) == "asubuhi"
    assert time_of_day("London", now=early) == "usiku"


def test_mood_offsets_are_bounded_and_condition_aware():
    assert mood_offset("dhoruba") < mood_offset("angavu")
    assert mood_offset("mvua") < 0 < mood_offset("angavu")
    assert mood_offset("unknown") == 0.0
    for _, offset in CONDITION_MOOD_OFFSET.items():
        assert -1.0 <= offset <= 1.0


@pytest.mark.asyncio
async def test_mock_feed_is_deterministic():
    feed = MockWeatherFeed()
    a = await feed.fetch("Dar es Salaam")
    b = await feed.fetch("Dar es Salaam")
    assert a["condition"] == b["condition"]
    assert a["source"] == "mock"
    assert a["time_of_day"] == b["time_of_day"]


def test_openweather_condition_mapping():
    assert OpenWeatherFeed._map_condition("Thunderstorm") == "dhoruba"
    assert OpenWeatherFeed._map_condition("Clear") == "angavu"
    assert OpenWeatherFeed._map_condition("Rain") == "mvua"
    assert OpenWeatherFeed._map_condition("Snow") == "baridi"


def test_feed_factory_prefers_real_when_key_set(monkeypatch):
    import weather_sync.meteorological_feed as mod

    monkeypatch.setattr(
        "weather_sync.meteorological_feed.get_settings",
        lambda: type("S", (), {"openweather_api_key": "abc"})(),
    )
    mod._weather_feed = None  # reset cache
    assert isinstance(get_weather_feed(), OpenWeatherFeed)

    monkeypatch.setattr(
        "weather_sync.meteorological_feed.get_settings",
        lambda: type("S", (), {"openweather_api_key": ""})(),
    )
    mod._weather_feed = None  # reset cache
    assert isinstance(get_weather_feed(), MockWeatherFeed)


def test_weather_bias_stays_in_bounds():
    offset = CONDITION_MOOD_OFFSET["dhoruba"]
    biased = clamp(0.8 + offset)
    assert -1.0 <= biased <= 1.0
