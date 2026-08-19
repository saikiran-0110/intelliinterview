"""Shared pydantic helpers — flexible emails for local/dummy accounts."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL_RE = re.compile(
    r"^[^@\s]+@([^@\s]+\.[^@\s]+|localhost|local|test|example|invalid)$",
    re.IGNORECASE,
)


def normalize_flexible_email(value: str) -> str:
    """
    Accept real emails and common dummy/dev addresses (e.g. user@test.com, a@b.local).
    Stricter than a free-form string, looser than EmailStr for student demos.
    """
    email = (value or "").strip().lower()
    if not email or not _EMAIL_RE.match(email):
        # Fallback: require a single @ with non-empty local and domain parts.
        if "@" not in email:
            raise ValueError("Enter a valid email address")
        local, _, domain = email.partition("@")
        if not local or not domain or " " in email:
            raise ValueError("Enter a valid email address")
    return email


FlexibleEmail = Annotated[str, AfterValidator(normalize_flexible_email)]
