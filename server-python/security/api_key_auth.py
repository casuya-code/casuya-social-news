"""API key authentication. Clients send `X-API-Key` (no browser origin).

Operator sessions may authenticate with a JWT access token instead via
`Authorization: Bearer <token>` — this keeps the API-key contract for the
Godot client while letting authenticated operators use the same endpoints.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.security import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param

from api.errors import UnauthorizedError
from config.settings import get_settings
from security.jwt import verify_access_token

_settings = get_settings()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(request: Request) -> str:
    """FastAPI dependency validating the API key. Returns the key on success."""
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == _settings.api_key:
        return api_key

    # Alternative: an operator JWT access token.
    auth = request.headers.get("Authorization", "")
    scheme, token = get_authorization_scheme_param(auth)
    if scheme.lower() == "bearer" and token:
        verify_access_token(token)
        return "jwt-operator"

    raise UnauthorizedError("Invalid or missing API key")
