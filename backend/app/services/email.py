"""Email delivery with SMTP; failures are logged quietly and never raised."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send(self, to_email: str, subject: str, body: str) -> bool:
        """
        Attempt to send email. Always returns True/False and never raises.
        OTP/dev flows should still print codes to the console separately.
        """
        to_email = (to_email or "").strip()
        if not to_email:
            logger.warning("EMAIL skipped: empty recipient subject=%s", subject)
            return False

        # Always mirror outbound mail in logs for local debugging.
        logger.info("EMAIL attempt to=%s subject=%s", to_email, subject)
        print(f"[IntelliInterview EMAIL] to={to_email} subject={subject}", flush=True)

        if not settings.smtp_host:
            logger.info("EMAIL (console-only, no SMTP host): to=%s\n%s", to_email, body)
            return True

        message = EmailMessage()
        message["From"] = settings.smtp_from_email or settings.smtp_username
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
            logger.info("EMAIL sent to=%s subject=%s", to_email, subject)
            return True
        except Exception as exc:  # noqa: BLE001 - never break auth/notify flows on mail failure
            # Dummy / unreachable addresses are expected in local testing.
            logger.warning("EMAIL failed silently to=%s subject=%s error=%s", to_email, subject, exc)
            print(
                f"[IntelliInterview EMAIL] failed silently to={to_email} error={exc}",
                flush=True,
            )
            return False
