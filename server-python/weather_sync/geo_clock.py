"""World clock (Feature #14): time-of-day bucket for a location.

The drama engine runs on "world time" — a script's time_of_day (asubuhi /
mchana / usiku) comes from the location the news story is set in, not the
server's wall clock. A small offset map keeps this dependency-free and
testable; extend with more cities as the world grows.
"""

from __future__ import annotations

from datetime import UTC, datetime

_UTC_OFFSETS = {
    "dar es salaam": 3,
    "dodoma": 3,
    "nairobi": 3,
    "kampala": 3,
    "kigali": 2,
    "lagos": 1,
    "accra": 0,
    "london": 0,
    "new york": -4,
}

TIME_OF_DAY_LABELS = ("asubuhi", "mchana", "usiku")


def utc_offset_hours(location: str) -> int:
    """Best-effort UTC offset for a city name (defaults to UTC)."""
    return _UTC_OFFSETS.get(location.strip().lower(), 0)


def time_of_day(location: str, *, now: datetime | None = None) -> str:
    """Map a location + instant to asubuhi / mchana / usiku.

    Buckets: 05:00–11:59 asubuhi, 12:00–17:59 mchana, otherwise usiku.
    """
    current = now or datetime.now(UTC)
    local_hour = (current.hour + utc_offset_hours(location)) % 24
    if 5 <= local_hour < 12:
        return "asubuhi"
    if 12 <= local_hour < 18:
        return "mchana"
    return "usiku"
