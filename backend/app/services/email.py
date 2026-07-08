"""Email sending abstraction.

Two implementations:
  - ``ResendEmailService`` — real delivery via the Resend HTTP API. Active
    whenever ``RESEND_API_KEY`` is configured.
  - ``LoggingEmailService`` — dev default; writes the email to the app log so
    local flows work end-to-end without a provider.

Routes depend on the abstract type via ``get_email_service``, so swapping
providers (SendGrid, Postmark, SMTP…) is a one-function change.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import requests

from app.core.config import settings

logger = logging.getLogger("app.services.email")


class EmailService(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class LoggingEmailService(EmailService):
    """Dev-friendly default: prints the email to the log instead of sending."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("[EMAIL] To: %s | Subject: %s\n%s", to, subject, body)


class ResendEmailService(EmailService):
    """Delivers via https://resend.com — a single POST per message.

    Raises for non-2xx responses so callers see delivery failures instead of
    silently losing verification / reset emails.
    """

    _ENDPOINT = "https://api.resend.com/emails"
    _TIMEOUT_S = 10

    def __init__(self, api_key: str, from_address: str):
        self._api_key = api_key
        self._from = from_address

    def send(self, *, to: str, subject: str, body: str) -> None:
        response = requests.post(
            self._ENDPOINT,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"from": self._from, "to": [to], "subject": subject, "text": body},
            timeout=self._TIMEOUT_S,
        )
        if not response.ok:
            logger.error(
                "Resend delivery failed (%s): %s", response.status_code, response.text[:500]
            )
            response.raise_for_status()
        logger.info("[EMAIL sent via Resend] To: %s | Subject: %s", to, subject)


def _build_default() -> EmailService:
    if settings.RESEND_API_KEY:
        return ResendEmailService(
            api_key=settings.RESEND_API_KEY,
            from_address=settings.EMAIL_FROM,
        )
    return LoggingEmailService()


_default_service: EmailService = _build_default()


def get_email_service() -> EmailService:
    """FastAPI dependency for injecting the email service into routes."""
    return _default_service
