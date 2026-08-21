"""Password hashing utilities using bcrypt directly.

passlib is unmaintained (last release 2020) and crashes with bcrypt>=4.1.
We use the bcrypt module directly — same algorithm, no中间层.
"""

from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plaintext password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check whether *plain* matches the stored bcrypt *hashed* value."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
