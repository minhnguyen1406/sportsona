"""Integration tests for /api/v1/auth/* routes using TestClient."""

from __future__ import annotations

from datetime import timedelta

from app.auth.security import create_access_token
from app.models import User
from tests._seed import make_user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_creates_user(self, client, db_session):
        response = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "supersecret1",
        })

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "new@example.com"
        assert body["username"] == "newuser"
        assert body["is_active"] is True
        assert body["is_superuser"] is False
        assert body["is_verified"] is False
        assert "hashed_password" not in body  # never leaked
        assert db_session.query(User).count() == 1

    def test_password_is_hashed_not_stored_plaintext(self, client, db_session):
        response = client.post("/api/v1/auth/register", json={
            "email": "h@example.com",
            "username": "hashtest",
            "password": "supersecret1",
        })
        assert response.status_code == 201
        user = db_session.query(User).filter_by(email="h@example.com").one()
        assert user.hashed_password != "supersecret1"
        assert user.hashed_password.startswith("$2")

    def test_duplicate_email_returns_409(self, client, db_session):
        make_user(db_session, email="taken@example.com", username="taken_u")
        db_session.commit()

        response = client.post("/api/v1/auth/register", json={
            "email": "taken@example.com",
            "username": "different",
            "password": "supersecret1",
        })
        assert response.status_code == 409

    def test_duplicate_username_returns_409(self, client, db_session):
        make_user(db_session, email="other@example.com", username="taken")
        db_session.commit()

        response = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "username": "taken",
            "password": "supersecret1",
        })
        assert response.status_code == 409

    def test_invalid_email_returns_422(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "username": "user",
            "password": "supersecret1",
        })
        assert response.status_code == 422

    def test_short_password_returns_422(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "u@example.com",
            "username": "user",
            "password": "short",
        })
        assert response.status_code == 422

    def test_short_username_returns_422(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "u@example.com",
            "username": "ab",
            "password": "supersecret1",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def test_returns_bearer_token_on_success(self, client, db_session):
        make_user(db_session, email="alice@example.com", username="alice", password="rightpw1")
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "alice@example.com", "password": "rightpw1"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    def test_wrong_password_returns_401(self, client, db_session):
        make_user(db_session, email="bob@example.com", username="bob", password="rightpw1")
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "bob@example.com", "password": "WRONG"},
        )
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "anything1"},
        )
        assert response.status_code == 401

    def test_inactive_user_returns_400(self, client, db_session):
        make_user(
            db_session,
            email="off@example.com", username="off", password="rightpw1",
            is_active=False,
        )
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "off@example.com", "password": "rightpw1"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------


def _login_token(client, db_session, **user_kwargs) -> str:
    user = make_user(db_session, **user_kwargs)
    db_session.commit()
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": user_kwargs.get("password", "correct horse battery staple")},
    )
    return response.json()["access_token"]


class TestReadCurrentUser:
    def test_returns_current_user(self, client, db_session):
        token = _login_token(client, db_session, email="me@example.com", username="me", password="rightpw1")

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

    def test_no_token_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_malformed_bearer_returns_401(self, client):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client, db_session):
        user = make_user(db_session, email="exp@example.com", username="exp")
        db_session.commit()
        token = create_access_token(subject=user.id, expires_delta=timedelta(seconds=-10))

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Token has expired"

    def test_token_for_deleted_user_returns_401(self, client, db_session):
        # Issue a token for an ID that does not exist in the DB
        token = create_access_token(subject=99999)

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_with_non_integer_subject_returns_401(self, client):
        token = create_access_token(subject="not-an-int")
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_missing_subject_returns_401(self, client):
        import jwt as _jwt
        from app.core.config import settings

        token = _jwt.encode({"foo": "bar"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_inactive_user_returns_400(self, client, db_session):
        user = make_user(
            db_session, email="inactive@example.com", username="inactive", is_active=False,
        )
        db_session.commit()
        token = create_access_token(subject=user.id)

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400
