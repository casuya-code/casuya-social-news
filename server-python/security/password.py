"""Password hashing utilities using passlib + bcrypt."""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plaintext password."""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check whether *plain* matches the stored bcrypt *hashed* value."""
    return _pwd_ctx.verify(plain, hashed)
