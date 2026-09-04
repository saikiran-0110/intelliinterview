from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.email import EmailService
from app.services.scheduling import SchedulingService


def test_email_skipped_for_empty_recipient():
    assert EmailService().send("", "Subject", "Body") is False


def test_email_console_only_when_no_smtp_host(monkeypatch):
    from app.services import email as email_module

    monkeypatch.setattr(email_module.settings, "smtp_host", "")
    assert EmailService().send("user@test.com", "Hello", "Body") is True


def test_email_returns_false_when_smtp_fails():
    service = EmailService()
    with patch("app.services.email.smtplib.SMTP", side_effect=OSError("unreachable")):
        assert service.send("user@test.com", "Hello", "Body") is False


def test_email_sends_when_smtp_succeeds():
    server = MagicMock()
    server.__enter__.return_value = server
    server.__exit__.return_value = False
    with patch("app.services.email.smtplib.SMTP", return_value=server) as smtp:
        assert EmailService().send("user@test.com", "Hello", "Thanks") is True
    smtp.assert_called_once()
    server.starttls.assert_called_once()
    server.login.assert_called_once()
    server.send_message.assert_called_once()


def test_suggest_slots_skips_weekend_and_honours_hours():
    service = SchedulingService()
    # Saturday 8 May 2026 09:00 UTC
    start = datetime(2026, 5, 8, 9, 0, tzinfo=timezone.utc)
    slots = service.suggest_slots(start_from=start, count=3, duration_minutes=45, hour_start=10, hour_end=16)
    assert len(slots) == 3
    for begins, ends in slots:
        assert begins.weekday() < 5
        assert 10 <= begins.hour < 16
        assert (ends - begins).total_seconds() == 45 * 60
