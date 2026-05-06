"""One-time tokens (email verification, password reset) and refresh-token
revocation list helpers.

One-time tokens use SHA-256 of the secret as the lookup key so the DB never
holds the plaintext — leaking the table does not leak active tokens.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import OneTimeToken, RevokedRefreshToken


PURPOSE_EMAIL_VERIFICATION = "email_verification"
PURPOSE_PASSWORD_RESET = "password_reset"

EMAIL_VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(hours=1)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_one_time_token(
    db: Session,
    *,
    user_id: int,
    purpose: str,
    ttl: timedelta,
) -> str:
    """Create and persist a single-use token; return the plaintext value."""
    raw = secrets.token_urlsafe(48)
    db.add(
        OneTimeToken(
            token_hash=_hash_token(raw),
            user_id=user_id,
            purpose=purpose,
            expires_at=datetime.utcnow() + ttl,
        )
    )
    db.flush()
    return raw


def consume_one_time_token(
    db: Session, *, token: str, purpose: str
) -> OneTimeToken | None:
    """Look up an unused, unexpired token; mark it used on success.

    Caller is responsible for ``db.commit()`` — keeping the side-effect
    explicit lets the caller bundle additional changes (flipping
    ``is_verified``, hashing a new password) into the same transaction.
    """
    record = (
        db.query(OneTimeToken)
        .filter(
            OneTimeToken.token_hash == _hash_token(token),
            OneTimeToken.purpose == purpose,
        )
        .first()
    )
    if record is None:
        return None
    if record.used_at is not None:
        return None
    if record.expires_at < datetime.utcnow():
        return None
    record.used_at = datetime.utcnow()
    return record


# --- Refresh-token revocation ---


def is_jti_revoked(db: Session, jti: str) -> bool:
    return (
        db.query(RevokedRefreshToken)
        .filter(RevokedRefreshToken.jti == jti)
        .first()
        is not None
    )


def revoke_jti(db: Session, *, jti: str, expires_at: datetime) -> None:
    """Add a jti to the revocation list. Idempotent."""
    if is_jti_revoked(db, jti):
        return
    db.add(RevokedRefreshToken(jti=jti, expires_at=expires_at))
    db.flush()
