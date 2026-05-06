"""Tests for /auth/logout and refresh-token revocation."""

from __future__ import annotations

from app.auth.security import create_access_token, create_refresh_token, decode_token
from app.auth.tokens import is_jti_revoked
from app.models import RevokedRefreshToken
from tests._seed import make_user


class TestLogout:
    def test_revokes_jti(self, client, db_session):
        user = make_user(db_session, email="lo@example.com", username="logouter")
        db_session.commit()
        token = create_refresh_token(subject=user.id)
        jti = decode_token(token)["jti"]

        response = client.post("/api/v1/auth/logout", json={"refresh_token": token})

        assert response.status_code == 204
        # Use a fresh fetch via the test session
        assert is_jti_revoked(db_session, jti)

    def test_logout_invalid_token_is_204(self, client):
        # Idempotent — no error on garbage input
        response = client.post(
            "/api/v1/auth/logout", json={"refresh_token": "not-a-jwt"}
        )
        assert response.status_code == 204

    def test_logout_with_access_token_does_nothing(self, client, db_session):
        user = make_user(db_session, email="ax@example.com", username="ax_logout")
        db_session.commit()
        access = create_access_token(subject=user.id)

        response = client.post("/api/v1/auth/logout", json={"refresh_token": access})

        assert response.status_code == 204
        # No revocation row was added
        assert db_session.query(RevokedRefreshToken).count() == 0

    def test_logout_with_refresh_missing_jti_is_no_op(self, client, db_session):
        # Forge a refresh-shaped JWT without a jti — logout should accept it
        # silently and not crash.
        import jwt as _jwt
        from datetime import datetime, timedelta, timezone
        from app.auth.security import REFRESH_TOKEN_TYPE
        from app.core.config import settings

        token = _jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
                "type": REFRESH_TOKEN_TYPE,
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        response = client.post("/api/v1/auth/logout", json={"refresh_token": token})
        assert response.status_code == 204
        assert db_session.query(RevokedRefreshToken).count() == 0


class TestRevokeJtiIdempotent:
    def test_double_revoke_is_noop(self, db_session):
        from datetime import datetime, timedelta
        from app.auth.tokens import revoke_jti
        from app.models import RevokedRefreshToken

        jti = "some-test-jti"
        expires = datetime.utcnow() + timedelta(minutes=10)
        revoke_jti(db_session, jti=jti, expires_at=expires)
        revoke_jti(db_session, jti=jti, expires_at=expires)  # idempotent
        db_session.commit()

        assert db_session.query(RevokedRefreshToken).filter_by(jti=jti).count() == 1


class TestRefreshRevocation:
    def test_old_jti_revoked_after_refresh(self, client, db_session):
        user = make_user(db_session, email="rr@example.com", username="rr_user")
        db_session.commit()
        old_refresh = create_refresh_token(subject=user.id)
        old_jti = decode_token(old_refresh)["jti"]

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert response.status_code == 200
        # Old jti now in revocation list
        assert is_jti_revoked(db_session, old_jti)

    def test_replay_of_used_refresh_token_returns_401(self, client, db_session):
        user = make_user(db_session, email="rp@example.com", username="rp_user")
        db_session.commit()
        old_refresh = create_refresh_token(subject=user.id)

        # First refresh succeeds
        first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert first.status_code == 200

        # Reusing the same refresh token must fail — its jti is revoked
        second = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert second.status_code == 401

    def test_logout_then_refresh_returns_401(self, client, db_session):
        user = make_user(db_session, email="lr@example.com", username="lr_user")
        db_session.commit()
        token = create_refresh_token(subject=user.id)

        client.post("/api/v1/auth/logout", json={"refresh_token": token})

        # Now this refresh token is in the revocation list
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401
