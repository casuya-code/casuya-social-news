"""Weather endpoint: current world-time + meteorological context.

GET /api/v1/weather — the sky the drama engine is currently writing under.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from security.api_key_auth import verify_api_key
from weather_sync.geo_clock import time_of_day
from weather_sync.meteorological_feed import get_weather_feed

router = APIRouter(dependencies=[Depends(verify_api_key)])


class WeatherResponse(BaseModel):
    location: str = ""
    condition: str = ""
    mood_offset: float = 0.0
    time_of_day: str = ""
    source: str = "mock"
    captured_at: str | None = None
    temp: float | None = None


@router.get("", response_model=WeatherResponse)
async def current_weather(
    location: str = Query(default="Dar es Salaam", min_length=2, max_length=128),
) -> WeatherResponse:
    """Return the active weather snapshot for a location."""
    weather = await get_weather_feed().fetch(location)
    weather["time_of_day"] = time_of_day(location)
    return WeatherResponse(**weather)
