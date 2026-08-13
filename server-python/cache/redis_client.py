"""Cache abstraction: Redis when available, in-memory dict fallback otherwise.

L1 cache (script generation results) lives here. TTL-based eviction mirrors
the README retention policy (news/scripts 24h). Degrades gracefully: if
Redis is unreachable at call time, requests fall back to in-memory storage.
"""

from __future__ import annotations

import asyncio
import time

from config.logging_config import get_logger
from config.settings import get_settings

_logger = get_logger("cache")
_settings = get_settings()

_default_ttl_seconds = 24 * 60 * 60  # 24h retention


class MemoryCache:
    """Process-local cache with TTL. Used when Redis is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, object]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() > expires_at:
            await self.delete(key)
            return None
        return value

    async def set(self, key: str, value: object, ttl: int = _default_ttl_seconds) -> None:
        async with self._lock:
            self._store[key] = (time.monotonic() + ttl, value)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None


class RedisCache:
    """Redis-backed cache. Falls back to MemoryCache on connection errors."""

    def __init__(self) -> None:
        import redis.asyncio as aioredis

        self._client = aioredis.from_url(_settings.redis_url, decode_responses=True)
        self._fallback = MemoryCache()

    async def _with_fallback(self, key: str, op: str, *args, **kwargs):
        try:
            return await getattr(self._client, op)(key, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - Redis down → degrade
            _logger.warning("cache_degraded_to_memory", op=op, error=str(exc))
            return await getattr(self._fallback, op)(key, *args, **kwargs)

    async def get(self, key: str) -> object | None:
        import json

        try:
            value = await self._client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return value
        except Exception:  # noqa: BLE001 - Redis down → degrade
            return await self._fallback.get(key)

    async def set(self, key: str, value: object, ttl: int = _default_ttl_seconds) -> None:
        import json

        try:
            payload = json.dumps(value) if not isinstance(value, str | bytes) else value
            await self._client.set(key, payload, ex=ttl)
        except Exception:  # noqa: BLE001 - Redis down → degrade
            _logger.warning("cache_degraded_to_memory", op="set")
            await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self._with_fallback(key, "delete")

    async def exists(self, key: str) -> bool:
        try:
            return bool(await self._client.exists(key))
        except Exception:  # noqa: BLE001
            return await self._fallback.exists(key)


def _make_cache():
    try:
        return RedisCache()
    except Exception:  # noqa: BLE001 - fall back when Redis is absent
        return MemoryCache()


cache = _make_cache()
