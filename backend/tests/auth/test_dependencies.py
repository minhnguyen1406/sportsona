"""Unit tests for the auth dependency callables.

These call the dependency functions directly (not through TestClient) to
exercise active/superuser branches without needing a route.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth.dependencies import (
    get_current_active_user,
    get_current_superuser,
)
from app.models import User


def _user(*, is_active=True, is_superuser=False) -> User:
    return User(
        id=1,
        email="x@example.com",
        username="x",
        hashed_password="x",
        is_active=is_active,
        is_superuser=is_superuser,
    )


class TestGetCurrentActiveUser:
    def test_returns_user_when_active(self):
        u = _user(is_active=True)
        assert get_current_active_user(u) is u

    def test_raises_400_when_inactive(self):
        with pytest.raises(HTTPException) as exc:
            get_current_active_user(_user(is_active=False))
        assert exc.value.status_code == 400
        assert exc.value.detail == "Inactive user"


class TestGetCurrentSuperuser:
    def test_returns_user_when_superuser(self):
        u = _user(is_superuser=True)
        assert get_current_superuser(u) is u

    def test_raises_403_when_not_superuser(self):
        with pytest.raises(HTTPException) as exc:
            get_current_superuser(_user(is_superuser=False))
        assert exc.value.status_code == 403
