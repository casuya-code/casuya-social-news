"""JWT auth endpoints: login, refresh, me.

POST /api/v1/auth/login    — operator credentials → {access_token, refresh_token}
POST /api/v1/auth/refresh  — refresh token → new access token
GET  /api/v1/auth/me       — access token → operator claims
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from api.errors import UnauthorizedError
from config.logging_config import get_logger
from config.settings import get_settings
from security.jwt import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
)

_logger = get_logger("api.auth")
_settings = get_settings()

router = APIRouter(tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def _credentials(
    creds: HTTPAuthorizationCredentials | None,
) -> str:
    """Extract the bearer token from auth headers."""
    if creds is None or not creds.credentials:
        raise UnauthorizedError("Bearer token required")
    return creds.credentials


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Exchange operator credentials for an access + refresh token pair."""
    if payload.username != _settings.admin_username or payload.password != _settings.admin_password:
        _logger.warning("login_failed", username=payload.username)
        raise UnauthorizedError("Invalid username or password")

    _logger.info("login_success", username=payload.username)
    return TokenResponse(
        access_token=create_access_token(),
        refresh_token=create_refresh_token(),
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> TokenResponse:
    """Rotate a refresh token into a fresh token pair."""
    token = _credentials(creds)
    decode_token(token, expected_type=TOKEN_TYPE_REFRESH)
    _logger.info("token_refreshed")
    return TokenResponse(
        access_token=create_access_token(),
        refresh_token=create_refresh_token(),
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me")
async def me(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Return the authenticated operator's token claims."""
    token = _credentials(creds)
    payload = verify_access_token(token)
    return {
        "sub": payload["sub"],
        "token_type": payload.get("type"),
        "expires_at": payload.get("exp"),
    }
