"""Password hashing and JWT token primitives.

Uses bcrypt for password hashing and HS256 JWTs. Both keys/algorithms come
from ``app.core.config.settings`` so deployments can override via env vars.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt. Caller must enforce the 72-byte input limit."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Issue a signed JWT.

    ``subject`` lands in the standard ``sub`` claim and is the canonical
    user identifier.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate signature + expiry and return claims.

    Raises ``jwt.ExpiredSignatureError`` if the token has expired and
    ``jwt.InvalidTokenError`` (or a subclass) for any other validation
    failure. Callers should let those propagate so the dependency layer
    can convert them to HTTP 401.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
