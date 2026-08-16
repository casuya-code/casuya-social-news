"""JWT creation and verification (README auth: E4002 JWT expired).

Operator-style login flow: exchange credentials for a short-lived access
token plus a long-lived refresh token. User credentials are stored in the
``users`` table (bcrypt-hashed). Settings-based fallback exists for
offline / first-boot scenarios.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt

from api.errors import TokenExpiredError, UnauthorizedError
from config.logging_config import get_logger
from config.settings import get_settings

_logger = get_logger("security.jwt")
_settings = get_settings()

ACCESS_TOKEN_SUBJECT = "casuya-operator"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _encode(payload: dict, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    to_encode = {
        **payload,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(to_encode, _settings.jwt_secret_key, algorithm=_settings.jwt_algorithm)


def create_access_token(subject: str = ACCESS_TOKEN_SUBJECT) -> str:
    """Short-lived access token for the operator session."""
    return _encode(
        {"sub": subject, "type": TOKEN_TYPE_ACCESS},
        timedelta(minutes=_settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(subject: str = ACCESS_TOKEN_SUBJECT) -> str:
    """Long-lived refresh token used to mint new access tokens."""
    return _encode(
        {"sub": subject, "type": TOKEN_TYPE_REFRESH},
        timedelta(days=_settings.jwt_refresh_token_expire_days),
    )


def decode_token(token: str, *, expected_type: str = TOKEN_TYPE_ACCESS) -> dict[str, Any]:
    """Verify a token's signature, expiry, and type. Raises APIError on failure."""
    try:
        payload = jwt.decode(token, _settings.jwt_secret_key, algorithms=[_settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        _logger.warning("jwt_expired")
        raise TokenExpiredError("Token has expired") from exc
    except JWTError as exc:
        _logger.warning("jwt_invalid", reason=str(exc))
        raise UnauthorizedError("Invalid or malformed token") from exc

    if payload.get("type") != expected_type:
        _logger.warning("jwt_wrong_type", expected=expected_type, got=payload.get("type"))
        raise UnauthorizedError("Invalid token type for this endpoint")

    if payload.get("sub") is None:
        raise UnauthorizedError("Token has no subject")

    return payload


def verify_access_token(token: str) -> dict[str, Any]:
    """Dependency-friendly access-token validator."""
    return decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
