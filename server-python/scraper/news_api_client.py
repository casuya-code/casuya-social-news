"""Real News API client (newsapi.org). Falls back to MockFeed without a key.

Uses the `NEWS_API_KEY` setting. Search query targets Swahili + East Africa
so the engine stays topical. Runs in a thread via asyncio.to_thread since
httpx is blocking in the sync client.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx

from config.logging_config import get_logger
from config.settings import get_settings
from scraper.mock_feed import MockFeed

_logger = get_logger("scraper.news_api")
_settings = get_settings()

_NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"
_QUERY = "Tanzania OR Kenya OR Uganda OR Swahili"
_RETRY_DELAYS = (1, 2, 4)


class NewsApiClient:
    """Fetch East African news via News API, with simple retry."""

    def __init__(self) -> None:
        self._api_key = _settings.news_api_key
        self._fallback = MockFeed()

    async def fetch_latest(self, limit: int = 10) -> list[dict]:
        if not self._api_key:
            _logger.warning("news_api_key not set; using mock feed")
            return await self._fallback.fetch_latest(limit)

        params = {
            "q": _QUERY,
            "language": "sw",
            "sortBy": "publishedAt",
            "pageSize": limit,
            "apiKey": self._api_key,
        }
        since = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        params["from"] = since

        last_error: Exception | None = None
        for delay in _RETRY_DELAYS:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(_NEWS_API_ENDPOINT, params=params)
                    response.raise_for_status()
                articles = response.json().get("articles", [])
                _logger.info("news_api_fetch_ok", count=len(articles))
                return articles
            except Exception as exc:  # noqa: BLE001 - retry then degrade
                last_error = exc
                _logger.warning("news_api_retry", delay=delay, error=str(exc))
                await asyncio.sleep(delay)

        _logger.error("news_api_failed", error=str(last_error))
        return await self._fallback.fetch_latest(limit)
