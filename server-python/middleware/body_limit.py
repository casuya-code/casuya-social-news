"""Request body size limit middleware.

Rejects requests whose Content-Length exceeds a configurable maximum.
Defaults to 1 MB, which is generous for the JSON payloads this API
accepts. Prevents memory exhaustion from malicious oversized bodies.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from starlette.responses import JSONResponse

from config.logging_config import get_logger

_logger = get_logger("middleware.body_limit")

DEFAULT_MAX_BYTES = 1 * 1024 * 1024  # 1 MB


class BodySizeLimitMiddleware:
    """ASGI middleware that rejects oversized request bodies."""

    def __init__(self, app: Any, *, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        self.app = app
        self._max_bytes = max_bytes

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[Any]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = scope.get("headers", [])
        for name, value in content_length:
            if name == b"content-length":
                try:
                    size = int(value)
                except ValueError:
                    await self.app(scope, receive, send)
                    return
                if size > self._max_bytes:
                    _logger.warning("request_body_too_large", size=size, limit=self._max_bytes)
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "status_code": 413,
                            "message": f"Request body too large (max {self._max_bytes} bytes)",
                            "error_code": "E0000",
                            "request_id": "",
                            "data": None,
                        },
                    )
                    await response(scope, receive, send)
                    return
                break

        await self.app(scope, receive, send)
