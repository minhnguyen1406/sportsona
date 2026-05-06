"""Tests for the refresh token flow."""

from __future__ import annotations

from datetime import timedelta

import jwt as _jwt

from app.auth.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from tests._seed import make_user


class TestTokenTypeClaim:
    def test_access_token_has_access_type(self):
        token = create_access_token(subject=1)
        claims = decode_token(token)
        assert claims["type"] == ACCESS_TOKEN_TYPE

    def test_refresh_token_has_refresh_type(self):
        token = create_refresh_token(subject=1)
        claims = decode_token(token)
        assert claims["type"] == REFRESH_TOKEN_TYPE

    def test_decode_rejects_wrong_type(self):
        access = create_access_token(subject=1)
        import pytest
        with pytest.raises(_jwt.InvalidTokenError):
            decode_token(access, expected_type=REFRESH_TOKEN_TYPE)


class TestRefreshEndpoint:
    def test_exchanges_refresh_for_new_pair(self, client, db_session):
        user = make_user(db_session, email="r@example.com", username="refresher")
        db_session.commit()
        refresh_token = create_refresh_token(subject=user.id)

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        # New tokens are issued — should differ from the input refresh
        assert body["refresh_token"] != refresh_token
        # The new access token must be type=access
        assert decode_token(body["access_token"])["type"] == ACCESS_TOKEN_TYPE

    def test_rejects_access_token_at_refresh_endpoint(self, client, db_session):
        user = make_user(db_session, email="b@example.com", username="bob_r")
        db_session.commit()
        access = create_access_token(subject=user.id)

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": access}
        )
        assert response.status_code == 401

    def test_rejects_expired_refresh(self, client, db_session):
        user = make_user(db_session, email="e@example.com", username="exp_r")
        db_session.commit()
        token = create_refresh_token(subject=user.id, expires_delta=timedelta(seconds=-10))

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_rejects_invalid_refresh(self, client):
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"}
        )
        assert response.status_code == 401

    def test_rejects_refresh_for_unknown_user(self, client):
        token = create_refresh_token(subject=99999)
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401

    def test_rejects_refresh_for_inactive_user(self, client, db_session):
        user = make_user(db_session, email="i@example.com", username="inactive_r", is_active=False)
        db_session.commit()
        token = create_refresh_token(subject=user.id)

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401

    def test_rejects_refresh_with_non_int_subject(self, client):
        token = _jwt.encode(
            {"sub": "not-an-int", "type": REFRESH_TOKEN_TYPE},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401
