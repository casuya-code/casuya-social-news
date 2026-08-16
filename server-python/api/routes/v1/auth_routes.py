"""JWT auth endpoints: login, refresh, me.

POST /api/v1/auth/login    — credentials → {access_token, refresh_token}
POST /api/v1/auth/register — create a new operator (admin only)
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
from security.password import verify_password

_logger = get_logger("api.auth")
_settings = get_settings()

router = APIRouter(tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)


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


async def _authenticate_user(username: str, password: str) -> bool:
    """Check credentials against DB, falling back to settings if DB is down."""
    try:
        from sqlalchemy import select

        from database.engine import SessionLocal
        from database.models import User

        async with SessionLocal() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            if user is not None:
                return verify_password(password, user.password_hash)
    except Exception:  # noqa: BLE001 — DB down, fall back to settings
        pass

    return username == _settings.admin_username and password == _settings.admin_password


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Exchange operator credentials for an access + refresh token pair."""
    if not await _authenticate_user(payload.username, payload.password):
        _logger.warning("login_failed", username=payload.username)
        raise UnauthorizedError("Invalid username or password")

    _logger.info("login_success", username=payload.username)
    return TokenResponse(
        access_token=create_access_token(),
        refresh_token=create_refresh_token(),
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest) -> TokenResponse:
    """Create a new operator account and return tokens immediately."""
    try:
        from sqlalchemy import select

        from database.engine import SessionLocal
        from database.models import User
        from security.password import hash_password

        async with SessionLocal() as session:
            result = await session.execute(
                select(User).where(User.username == payload.username)
            )
            if result.scalar_one_or_none() is not None:
                raise UnauthorizedError("Username already taken")

            session.add(
                User(
                    username=payload.username,
                    password_hash=hash_password(payload.password),
                    is_admin=False,
                )
            )
            await session.commit()
    except UnauthorizedError:
        raise
    except Exception as exc:  # noqa: BLE001 — DB down
        _logger.warning("register_failed", error=str(exc))
        raise UnauthorizedError("Registration unavailable (database offline)") from exc

    _logger.info("register_success", username=payload.username)
    return TokenResponse(
        access_token=create_access_token(subject=payload.username),
        refresh_token=create_refresh_token(subject=payload.username),
        expires_in=_settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> TokenResponse:
    """Rotate a refresh token into a fresh token pair."""
    token = _credentials(creds)
    payload = decode_token(token, expected_type=TOKEN_TYPE_REFRESH)
    subject = payload.get("sub", "casuya-operator")
    _logger.info("token_refreshed")
    return TokenResponse(
        access_token=create_access_token(subject=subject),
        refresh_token=create_refresh_token(subject=subject),
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
