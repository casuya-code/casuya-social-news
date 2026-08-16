"""Response envelope middleware — wraps 2xx JSON responses to match api_response.json.

Error responses are already wrapped by the exception handlers (handlers.py).
This middleware catches *success* responses and wraps them in the standard
envelope: ``{success, status_code, message, error_code, request_id, data}``.
"""

from __future__ import annotations

import json

from config.logging_config import get_logger
from middleware.request_id import get_request_id

_logger = get_logger("middleware.envelope")

# Routes that already return their own envelope or non-JSON and must be skipped.
_SKIP_PREFIXES = ("/storage", "/metrics", "/docs", "/openapi.json", "/redoc")


class ResponseEnvelopeMiddleware:
    """ASGI middleware that wraps 2xx JSON responses in the standard envelope."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip non-API paths, static files, docs, etc.
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            await self.app(scope, receive, send)
            return

        # Only wrap /api/ routes.
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        status_code = 200
        start_sent = False
        can_wrap = True
        response_headers: list[tuple[bytes, bytes]] = []

        async def send_with_envelope(message):
            nonlocal status_code, start_sent, can_wrap, response_headers

            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                response_headers = list(message.get("headers", []))

                # Only wrap 2xx JSON responses.
                if status_code < 200 or status_code >= 300:
                    can_wrap = False
                    start_sent = True
                    await send(message)
                    return

                # Check content-type for JSON.
                content_type = ""
                for name, value in response_headers:
                    if name == b"content-type":
                        content_type = value.decode("latin-1")
                        break

                if "application/json" not in content_type:
                    can_wrap = False
                    start_sent = True
                    await send(message)
                    return

                # Don't send start yet — wait for body so we can wrap.
                return

            if message["type"] == "http.response.body":
                if start_sent:
                    # Already forwarded start — just pass body through.
                    await send(message)
                    return

                body: bytes = message.get("body", b"")

                if can_wrap and body:
                    try:
                        original = json.loads(body)
                        wrapped = {
                            "success": True,
                            "status_code": status_code,
                            "message": "ok",
                            "error_code": None,
                            "request_id": get_request_id() or None,
                            "data": original,
                        }
                        wrapped_body = json.dumps(wrapped).encode("utf-8")

                        # Update Content-Length.
                        new_headers = []
                        for name, value in response_headers:
                            if name == b"content-length":
                                new_headers.append((name, str(len(wrapped_body)).encode("latin-1")))
                            else:
                                new_headers.append((name, value))

                        start_sent = True
                        await send({
                            "type": "http.response.start",
                            "status": status_code,
                            "headers": new_headers,
                        })
                        await send({
                            "type": "http.response.body",
                            "body": wrapped_body,
                            "more_body": message.get("more_body", False),
                        })
                        return
                    except (json.JSONDecodeError, TypeError):
                        pass  # Not valid JSON — send as-is

                # Not wrapped — forward original start + body now.
                start_sent = True
                await send({
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": response_headers,
                })
                await send(message)
                return

            await send(message)

        await self.app(scope, receive, send_with_envelope)
