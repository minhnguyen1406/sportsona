"""Tests for password reset flow."""

from __future__ import annotations

from datetime import timedelta

from app.auth.security import verify_password
from app.auth.tokens import (
    PASSWORD_RESET_TTL,
    PURPOSE_PASSWORD_RESET,
    issue_one_time_token,
)
from app.models import OneTimeToken, User
from app.services.email import EmailService, get_email_service
from tests._seed import make_user


class _CapturingEmailService(EmailService):
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


class TestForgotPassword:
    def test_known_email_sends_reset_link(self, client, db_session):
        from app.main import app

        capture = _CapturingEmailService()
        app.dependency_overrides[get_email_service] = lambda: capture

        make_user(db_session, email="forgot@example.com", username="forget_me")
        db_session.commit()

        response = client.post(
            "/api/v1/auth/password/forgot", json={"email": "forgot@example.com"}
        )

        assert response.status_code == 204
        assert len(capture.sent) == 1
        assert "reset-password?token=" in capture.sent[0]["body"]
        assert db_session.query(OneTimeToken).count() == 1

        del app.dependency_overrides[get_email_service]

    def test_unknown_email_still_returns_204_and_sends_nothing(self, client, db_session):
        # Anti-enumeration: response must be indistinguishable from the success case
        from app.main import app

        capture = _CapturingEmailService()
        app.dependency_overrides[get_email_service] = lambda: capture

        response = client.post(
            "/api/v1/auth/password/forgot", json={"email": "ghost@example.com"}
        )

        assert response.status_code == 204
        assert capture.sent == []
        assert db_session.query(OneTimeToken).count() == 0

        del app.dependency_overrides[get_email_service]

    def test_inactive_user_does_not_get_reset_email(self, client, db_session):
        from app.main import app

        capture = _CapturingEmailService()
        app.dependency_overrides[get_email_service] = lambda: capture

        make_user(db_session, email="off@example.com", username="off_user", is_active=False)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/password/forgot", json={"email": "off@example.com"}
        )

        assert response.status_code == 204
        assert capture.sent == []

        del app.dependency_overrides[get_email_service]


class TestResetPassword:
    def test_resets_password_with_valid_token(self, client, db_session):
        user = make_user(
            db_session, email="r@example.com", username="resetter", password="oldpw1234"
        )
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_PASSWORD_RESET,
            ttl=PASSWORD_RESET_TTL,
        )
        db_session.commit()

        response = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "newpw12345"},
        )

        assert response.status_code == 204
        db_session.expire_all()
        refreshed = db_session.query(User).filter_by(id=user.id).one()
        assert verify_password("newpw12345", refreshed.hashed_password)
        assert not verify_password("oldpw1234", refreshed.hashed_password)

    def test_invalid_token_returns_400(self, client):
        response = client.post(
            "/api/v1/auth/password/reset",
            json={"token": "garbage", "new_password": "newpw12345"},
        )
        assert response.status_code == 400

    def test_expired_token_returns_400(self, client, db_session):
        user = make_user(db_session, email="e@example.com", username="exp_pw")
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_PASSWORD_RESET,
            ttl=timedelta(seconds=-1),
        )
        db_session.commit()

        response = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "newpw12345"},
        )
        assert response.status_code == 400

    def test_used_token_cannot_be_reused(self, client, db_session):
        user = make_user(
            db_session, email="o@example.com", username="once_pw", password="oldpw1234"
        )
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_PASSWORD_RESET,
            ttl=PASSWORD_RESET_TTL,
        )
        db_session.commit()

        first = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "newpw12345"},
        )
        second = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "anotherpw1"},
        )
        assert first.status_code == 204
        assert second.status_code == 400

    def test_short_new_password_rejected(self, client, db_session):
        # Validation happens before token consumption
        user = make_user(db_session, email="s@example.com", username="short_pw")
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_PASSWORD_RESET,
            ttl=PASSWORD_RESET_TTL,
        )
        db_session.commit()

        response = client.post(
            "/api/v1/auth/password/reset",
            json={"token": token, "new_password": "tiny"},
        )
        assert response.status_code == 422
