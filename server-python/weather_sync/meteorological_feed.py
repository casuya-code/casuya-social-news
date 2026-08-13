"""Meteorological feed (Feature #30): weather as a mood input.

Weather is not decoration — it biases character mood. A thunderstorm nags
at the cast's spirits, bright sunshine lifts them. The offset feeds into
the mood-drift system so the drama reacts to its own sky.

No API key? A deterministic mock condition (seeded by location + clock)
keeps the loop working offline. With OPENWEATHER_API_KEY set, real data
is fetched and the mock is the fallback on any failure.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from config.logging_config import get_logger
from config.settings import get_settings
from weather_sync.geo_clock import time_of_day

_logger = get_logger("weather.met")

# condition -> mood offset in [-1, 1]
CONDITION_MOOD_OFFSET = {
    "mawingu": -0.1,  # overcast
    "mvua": -0.25,  # rain
    "dhoruba": -0.4,  # storm
    "joto": -0.05,  # hot
    "baridi": 0.0,  # cold
    "angavu": 0.2,  # clear
    "hewa_safi": 0.15,  # pleasant/breezy
}

_CONDITION_BY_PERIOD = {
    "asubuhi": "angavu",
    "mchana": "joto",
    "usiku": "baridi",
}

_DEFAULT_LOCATION = "Dar es Salaam"


class WeatherError(RuntimeError):
    """Raised when the real weather feed is unreachable (caller falls back)."""


def mood_offset(condition: str) -> float:
    """Weather condition → mood bias, defaulting to neutral."""
    return CONDITION_MOOD_OFFSET.get(condition, 0.0)


class MockWeatherFeed:
    """Deterministic offline weather: fixed by location + time of day."""

    def __init__(self, location: str = _DEFAULT_LOCATION) -> None:
        self.location = location

    async def fetch(self, location: str | None = None) -> dict:
        loc = location or self.location
        period = time_of_day(loc)
        condition = _CONDITION_BY_PERIOD[period]
        return {
            "location": loc,
            "condition": condition,
            "mood_offset": mood_offset(condition),
            "time_of_day": period,
            "source": "mock",
            "captured_at": datetime.now(UTC).isoformat(),
        }


class OpenWeatherFeed:
    """Real conditions via OpenWeatherMap; mock fallback on any failure."""

    def __init__(self, api_key: str, location: str = _DEFAULT_LOCATION) -> None:
        self.api_key = api_key
        self.location = location
        self._fallback = MockWeatherFeed(location)

    async def fetch(self, location: str | None = None) -> dict:
        loc = location or self.location
        params = {"q": loc, "appid": self.api_key, "units": "metric"}
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather", params=params
                )
                response.raise_for_status()
                data = response.json()
                condition = self._map_condition(data.get("weather", [{}])[0].get("main", ""))
                return {
                    "location": loc,
                    "condition": condition,
                    "mood_offset": mood_offset(condition),
                    "time_of_day": time_of_day(loc),
                    "temperature_c": data.get("main", {}).get("temp"),
                    "source": "openweather",
                    "captured_at": datetime.now(UTC).isoformat(),
                }
        except Exception as exc:  # noqa: BLE001 - degrade, never break the loop
            _logger.warning("weather_fetch_failed", error=str(exc), fallback="mock")
            return await self._fallback.fetch(loc)

    @staticmethod
    def _map_condition(openweather_main: str) -> str:
        return {
            "Clear": "angavu",
            "Clouds": "mawingu",
            "Rain": "mvua",
            "Drizzle": "mvua",
            "Thunderstorm": "dhoruba",
            "Snow": "baridi",
            "Mist": "mawingu",
            "Haze": "mawingu",
            "Fog": "mawingu",
        }.get(openweather_main, "hewa_safi")


def get_weather_feed() -> MockWeatherFeed | OpenWeatherFeed:
    """Provider factory — real feed when a key is configured, else mock."""
    api_key = get_settings().openweather_api_key
    if api_key:
        return OpenWeatherFeed(api_key)
    return MockWeatherFeed()
