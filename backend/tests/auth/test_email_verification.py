"""Tests for email verification flow."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.auth.security import create_access_token
from app.auth.tokens import (
    EMAIL_VERIFICATION_TTL,
    PURPOSE_EMAIL_VERIFICATION,
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


def _override_email(client_app, capture: _CapturingEmailService):
    """Override the email service dependency on the running app."""
    client_app.dependency_overrides[get_email_service] = lambda: capture


class TestRequestVerification:
    def test_requires_auth(self, client):
        assert client.post("/api/v1/auth/email/request-verification").status_code == 401

    def test_issues_token_and_sends_email(self, client, db_session):
        from app.main import app

        capture = _CapturingEmailService()
        _override_email(app, capture)

        user = make_user(db_session, email="v@example.com", username="verifier")
        db_session.commit()
        token = create_access_token(subject=user.id)

        response = client.post(
            "/api/v1/auth/email/request-verification",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204
        assert db_session.query(OneTimeToken).filter_by(user_id=user.id).count() == 1
        assert len(capture.sent) == 1
        assert capture.sent[0]["to"] == "v@example.com"
        assert "verify-email?token=" in capture.sent[0]["body"]

        del app.dependency_overrides[get_email_service]

    def test_already_verified_user_skipped(self, client, db_session):
        from app.main import app

        capture = _CapturingEmailService()
        _override_email(app, capture)

        user = make_user(db_session, email="vv@example.com", username="vverified", is_verified=True)
        db_session.commit()
        token = create_access_token(subject=user.id)

        response = client.post(
            "/api/v1/auth/email/request-verification",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204
        assert db_session.query(OneTimeToken).count() == 0
        assert capture.sent == []

        del app.dependency_overrides[get_email_service]


class TestVerifyEmail:
    def test_marks_user_verified(self, client, db_session):
        user = make_user(db_session, email="ve@example.com", username="ve_user")
        db_session.commit()
        raw_token = issue_one_time_token(
            db_session,
            user_id=user.id,
            purpose=PURPOSE_EMAIL_VERIFICATION,
            ttl=EMAIL_VERIFICATION_TTL,
        )
        db_session.commit()

        response = client.post("/api/v1/auth/email/verify", json={"token": raw_token})

        assert response.status_code == 204
        # Re-fetch via test session — verifies the request-side commit landed
        db_session.expire_all()
        assert db_session.query(User).filter_by(id=user.id).one().is_verified is True

    def test_invalid_token_returns_400(self, client):
        response = client.post("/api/v1/auth/email/verify", json={"token": "garbage"})
        assert response.status_code == 400

    def test_already_used_token_returns_400(self, client, db_session):
        user = make_user(db_session, email="vu@example.com", username="vu_user")
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_EMAIL_VERIFICATION,
            ttl=EMAIL_VERIFICATION_TTL,
        )
        db_session.commit()

        first = client.post("/api/v1/auth/email/verify", json={"token": token})
        second = client.post("/api/v1/auth/email/verify", json={"token": token})

        assert first.status_code == 204
        assert second.status_code == 400

    def test_expired_token_returns_400(self, client, db_session):
        user = make_user(db_session, email="ex@example.com", username="ex_user")
        db_session.commit()
        # Issue with negative TTL → already expired
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_EMAIL_VERIFICATION,
            ttl=timedelta(seconds=-1),
        )
        db_session.commit()

        response = client.post("/api/v1/auth/email/verify", json={"token": token})
        assert response.status_code == 400

    def test_token_with_wrong_purpose_returns_400(self, client, db_session):
        # A password-reset token must not work as an email-verification token
        from app.auth.tokens import PURPOSE_PASSWORD_RESET

        user = make_user(db_session, email="wp@example.com", username="wp_user")
        db_session.commit()
        token = issue_one_time_token(
            db_session, user_id=user.id, purpose=PURPOSE_PASSWORD_RESET,
            ttl=timedelta(hours=1),
        )
        db_session.commit()

        response = client.post("/api/v1/auth/email/verify", json={"token": token})
        assert response.status_code == 400
