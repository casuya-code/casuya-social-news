"""API key authentication. Clients send `X-API-Key` (no browser origin)."""

from __future__ import annotations

from fastapi import Request
from fastapi.security import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param

from api.errors import UnauthorizedError
from config.settings import get_settings

_settings = get_settings()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(request: Request) -> str:
    """FastAPI dependency validating the API key. Returns the key on success."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # Allow `Authorization: Bearer <key>` as an alternative.
        auth = request.headers.get("Authorization", "")
        _, api_key = get_authorization_scheme_param(auth)

    if not api_key or api_key != _settings.api_key:
        raise UnauthorizedError("Invalid or missing API key")
    return api_key
