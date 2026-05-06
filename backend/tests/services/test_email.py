"""Tests for the LoggingEmailService default implementation."""

from __future__ import annotations

import logging

from app.services.email import LoggingEmailService, get_email_service


def test_default_service_is_logging_service():
    assert isinstance(get_email_service(), LoggingEmailService)


def test_logging_service_writes_to_logger(caplog):
    service = LoggingEmailService()
    with caplog.at_level(logging.INFO, logger="app.services.email"):
        service.send(to="x@example.com", subject="Hi", body="hello")

    record = next(r for r in caplog.records if "[EMAIL]" in r.getMessage())
    assert "x@example.com" in record.getMessage()
    assert "Hi" in record.getMessage()
    assert "hello" in record.getMessage()
