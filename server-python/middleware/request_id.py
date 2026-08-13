"""Request ID middleware — assigns a UUID to every request for log correlation.

Implemented as pure ASGI (not BaseHTTPMiddleware) so the contextvar set here
propagates into the route handler, dependencies, and exception handlers, which
run in the same task/context.
"""

import contextvars
import uuid

CONTEXT_HEADER = "X-Request-ID"

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request ID (empty string outside a request)."""
    return _request_id_var.get()


class RequestIDMiddleware:
    """Generate or propagate a request ID and expose it via response header."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request_id = ""
        for header_name, value in scope.get("headers", []):
            if header_name == b"x-request-id":
                request_id = value.decode("latin-1")
                break
        if not request_id:
            request_id = uuid.uuid4().hex[:16]

        token = _request_id_var.set(request_id)

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((CONTEXT_HEADER.encode("latin-1"), request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            _request_id_var.reset(token)
