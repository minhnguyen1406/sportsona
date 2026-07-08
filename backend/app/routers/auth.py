"""Auth routes: register, login, refresh, logout, email verification, password reset."""

from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.rate_limit import limiter
from app.auth.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.auth.tokens import (
    EMAIL_VERIFICATION_TTL,
    PASSWORD_RESET_TTL,
    PURPOSE_EMAIL_VERIFICATION,
    PURPOSE_PASSWORD_RESET,
    consume_one_time_token,
    is_jti_revoked,
    issue_one_time_token,
    revoke_jti,
)
from app.core.config import settings
from app.core.database import get_db
from app.models import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserRead,
    VerifyEmailRequest,
)
from app.schemas.errors import RATE_LIMITED, UNAUTHORIZED
from app.services.email import EmailService, get_email_service


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# register / login
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses=RATE_LIMITED,
)
@limiter.limit("10/hour")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new user account.

    Returns 409 if the email or username is already taken. The new user
    starts active and unverified — call ``/email/request-verification``
    after login to send the verification email.
    """
    existing = (
        db.query(User)
        .filter((User.email == payload.email) | (User.username == payload.username))
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    responses={**UNAUTHORIZED, **RATE_LIMITED},
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """OAuth2 password flow. ``form_data.username`` is the user's email."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


# ---------------------------------------------------------------------------
# refresh / logout
# ---------------------------------------------------------------------------


def _decode_refresh_or_401(token: str) -> dict:
    try:
        return decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.post("/refresh", response_model=Token, responses=UNAUTHORIZED)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    """Exchange a valid refresh token for a new access + refresh pair.

    Rotates and revokes the old refresh token's ``jti`` so reuse of a
    leaked refresh token can be detected (the second use will 401).
    """
    claims = _decode_refresh_or_401(payload.refresh_token)

    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    jti = claims.get("jti")
    if jti is None or is_jti_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Revoke the OLD refresh-token jti before issuing a new pair so the
    # caller cannot reuse the previous token.
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None)
    revoke_jti(db, jti=jti, expires_at=expires_at)
    db.commit()

    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token. Idempotent — silently 204s for invalid input."""
    try:
        claims = decode_token(payload.refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    except jwt.InvalidTokenError:
        return  # nothing to revoke

    jti = claims.get("jti")
    if jti is None:
        return

    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None)
    revoke_jti(db, jti=jti, expires_at=expires_at)
    db.commit()


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserRead, responses=UNAUTHORIZED)
def read_current_user(user: User = Depends(get_current_active_user)) -> User:
    return user


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


@router.post(
    "/email/request-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**UNAUTHORIZED, **RATE_LIMITED},
)
@limiter.limit("5/hour")
def request_email_verification(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
):
    """Issue a verification token and email it to the current user.

    Idempotent for already-verified users (no email sent, returns 204).
    """
    if user.is_verified:
        return

    token = issue_one_time_token(
        db,
        user_id=user.id,
        purpose=PURPOSE_EMAIL_VERIFICATION,
        ttl=EMAIL_VERIFICATION_TTL,
    )
    db.commit()

    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    email.send(
        to=user.email,
        subject="Verify your Sportsona email",
        body=f"Click to verify your email: {link}\n\nThis link expires in 24 hours.",
    )


@router.post(
    "/email/verify",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RATE_LIMITED,
)
@limiter.limit("10/hour")
def verify_email(
    request: Request, payload: VerifyEmailRequest, db: Session = Depends(get_db)
):
    """Verify an email using the token from the verification link."""
    record = consume_one_time_token(
        db, token=payload.token, purpose=PURPOSE_EMAIL_VERIFICATION
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    record.user.is_verified = True
    db.commit()


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@router.post(
    "/password/forgot",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RATE_LIMITED,
)
@limiter.limit("5/hour")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    email: EmailService = Depends(get_email_service),
):
    """Send a password-reset email if the address corresponds to a user.

    Always returns 204 — never reveals whether the email is registered.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active:
        return

    token = issue_one_time_token(
        db,
        user_id=user.id,
        purpose=PURPOSE_PASSWORD_RESET,
        ttl=PASSWORD_RESET_TTL,
    )
    db.commit()

    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    email.send(
        to=user.email,
        subject="Reset your Sportsona password",
        body=(
            f"Click to reset your password: {link}\n\n"
            "This link expires in 1 hour. If you didn't request this, ignore this email."
        ),
    )


@router.post(
    "/password/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=RATE_LIMITED,
)
@limiter.limit("10/hour")
def reset_password(
    request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)
):
    """Reset a password using the token from the reset email."""
    record = consume_one_time_token(
        db, token=payload.token, purpose=PURPOSE_PASSWORD_RESET
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    record.user.hashed_password = hash_password(payload.new_password)
    db.commit()
