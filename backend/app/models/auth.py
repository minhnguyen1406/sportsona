"""Auth-related persistence: refresh-token revocation list and one-time tokens.

We use a single ``one_time_tokens`` table for email verification and
password reset since they share the same shape (hashed token + user + purpose
+ expiry + used flag). Revoked refresh tokens live in their own table because
they're keyed by the JWT's ``jti`` claim and need different lookup semantics.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class RevokedRefreshToken(Base):
    """A refresh-token ``jti`` that should be rejected from now on.

    Rows can be pruned periodically once ``expires_at`` is in the past —
    a JWT past its own ``exp`` is rejected by signature validation anyway.
    """

    __tablename__ = "revoked_refresh_tokens"

    jti = Column(String, primary_key=True)
    revoked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class OneTimeToken(Base):
    """A single-use token for an out-of-band verification flow.

    The ``token`` value the user receives is *not* stored — only its hash —
    so leaking the table doesn't leak active tokens.
    """

    __tablename__ = "one_time_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String, nullable=False, index=True)  # "email_verification" | "password_reset"
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")
