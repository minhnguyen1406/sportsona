"""Pydantic schemas for the auth flows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    # bcrypt silently truncates inputs above 72 bytes — cap here to make that explicit
    password: str = Field(min_length=8, max_length=72)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# JWTs are well under 1KB; capping bounds request size to deter DoS via large bodies.
_TOKEN_MAX_LEN = 1024


class RefreshRequest(BaseModel):
    refresh_token: str = Field(max_length=_TOKEN_MAX_LEN)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(max_length=_TOKEN_MAX_LEN)


class VerifyEmailRequest(BaseModel):
    token: str = Field(max_length=_TOKEN_MAX_LEN)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(max_length=_TOKEN_MAX_LEN)
    new_password: str = Field(min_length=8, max_length=72)


