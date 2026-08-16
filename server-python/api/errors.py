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


class EmotionTaggingError(APIError):
    status_code = 500
    error_code = "E1002"


class ScriptTimeoutError(APIError):
    status_code = 504
    error_code = "E1003"


class TTSQuotaError(APIError):
    status_code = 429
    error_code = "E2002"


class TTSWriteError(APIError):
    status_code = 500
    error_code = "E2003"


class NewsSourceError(APIError):
    status_code = 503
    error_code = "E5001"


class NewsRateLimitedError(APIError):
    status_code = 429
    error_code = "E5002"


class UnauthorizedError(APIError):
    status_code = 401
    error_code = "E4001"


class TokenExpiredError(APIError):
    status_code = 401
    error_code = "E4002"


class MigrationRequiredError(APIError):
    status_code = 409
    error_code = "E3003"
