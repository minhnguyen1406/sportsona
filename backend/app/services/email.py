"""Email sending abstraction.

The default implementation writes to the application log so dev environments
work end-to-end without an email provider. Swap in a real implementation
(SMTP, SendGrid, Resend, Postmark, …) by changing what ``get_email_service``
returns — routes depend on the abstract type, not the concrete impl.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("app.services.email")


class EmailService(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class LoggingEmailService(EmailService):
    """Dev-friendly default: prints the email to the log instead of sending."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("[EMAIL] To: %s | Subject: %s\n%s", to, subject, body)


_default_service: EmailService = LoggingEmailService()


def get_email_service() -> EmailService:
    """FastAPI dependency for injecting the email service into routes."""
    return _default_service
