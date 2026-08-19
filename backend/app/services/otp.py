"""One-time password challenges for registration and login."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import OtpChallenge, OtpPurpose
from app.services.email import EmailService
from app.services.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class OtpService:
    def __init__(self) -> None:
        self.email_service = EmailService()
        self.ttl_minutes = 10
        self.max_attempts = 5

    def issue(
        self,
        db: Session,
        *,
        email: str,
        purpose: OtpPurpose,
        payload: dict[str, Any] | None = None,
        subject: str,
        body_prefix: str,
    ) -> tuple[OtpChallenge, str]:
        email_norm = email.lower().strip()
        code = f"{secrets.randbelow(1_000_000):06d}"

        # Invalidate previous open challenges for this email/purpose.
        open_items = (
            db.query(OtpChallenge)
            .filter(
                OtpChallenge.email == email_norm,
                OtpChallenge.purpose == purpose,
                OtpChallenge.consumed_at.is_(None),
            )
            .all()
        )
        now = datetime.now(timezone.utc)
        for item in open_items:
            item.consumed_at = now
            db.add(item)

        challenge = OtpChallenge(
            email=email_norm,
            purpose=purpose,
            code_hash=hash_password(code),
            payload=payload,
            expires_at=now + timedelta(minutes=self.ttl_minutes),
            attempt_count=0,
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        # Always log OTP clearly for local/dev use without burning email quota.
        logger.info(
            "OTP CODE for %s (%s): %s (expires in %s minutes)",
            email_norm,
            purpose.value,
            code,
            self.ttl_minutes,
        )
        print(f"[IntelliInterview OTP] email={email_norm} purpose={purpose.value} code={code}", flush=True)

        body = (
            f"{body_prefix}\n\n"
            f"Your one-time passcode is: {code}\n"
            f"It expires in {self.ttl_minutes} minutes.\n\n"
            "If you did not request this, you can ignore this message."
        )
        # Send email when possible; failures are swallowed so dummy addresses still work.
        try:
            self.email_service.send(email_norm, subject, body)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OTP email send ignored for %s: %s", email_norm, exc)
        return challenge, code

    def verify(self, db: Session, *, email: str, purpose: OtpPurpose, code: str) -> OtpChallenge:
        email_norm = email.lower().strip()
        challenge = (
            db.query(OtpChallenge)
            .filter(
                OtpChallenge.email == email_norm,
                OtpChallenge.purpose == purpose,
                OtpChallenge.consumed_at.is_(None),
            )
            .order_by(OtpChallenge.created_at.desc())
            .first()
        )
        if challenge is None:
            raise ValueError("No active verification code. Request a new OTP.")

        now = datetime.now(timezone.utc)
        expires = challenge.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            raise ValueError("Verification code expired. Request a new OTP.")

        if challenge.attempt_count >= self.max_attempts:
            raise ValueError("Too many incorrect attempts. Request a new OTP.")

        challenge.attempt_count += 1
        db.add(challenge)
        db.commit()

        if not verify_password(code.strip(), challenge.code_hash):
            raise ValueError("Invalid verification code.")

        challenge.consumed_at = now
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        return challenge
