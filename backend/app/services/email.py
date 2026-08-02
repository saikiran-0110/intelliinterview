"""Email delivery with SMTP or console fallback for local development."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send(self, to_email: str, subject: str, body: str) -> bool:
        if not settings.smtp_host:
            logger.info("EMAIL (console): to=%s subject=%s\n%s", to_email, subject, body)
            return True

        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            return True
        except (OSError, smtplib.SMTPException) as exc:
            logger.warning("EMAIL failed to=%s error=%s", to_email, exc)
            return False
