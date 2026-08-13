"""Error code taxonomy and structured API exceptions.

Codes follow the README taxonomy:
  E1xxx NLP, E2xxx Voice/TTS, E3xxx Cache/DB, E4xxx Auth/Rate-limit, E5xxx Scraper.
"""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """Base error carrying the response envelope fields."""

    status_code: int = 500
    error_code: str = "E0000"

    def __init__(self, message: str, *, extra: dict[str, Any] | None = None) -> None:
        self.message = message
        self.extra = extra or {}
        super().__init__(message)


class NotFoundError(APIError):
    status_code = 404
    error_code = "E3001"


class TTSProviderError(APIError):
    status_code = 503
    error_code = "E2001"


class InvalidInputError(APIError):
    status_code = 422
    error_code = "E1001"


class RateLimitedError(APIError):
    status_code = 429
    error_code = "E4003"


class UnauthorizedError(APIError):
    status_code = 401
    error_code = "E4001"


class DatabaseError(APIError):
    status_code = 500
    error_code = "E3002"
