from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import OtpPurpose, UserRole


class RegisterRequest(BaseModel):
    """Legacy direct register (kept for compatibility). Prefer OTP register flow."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=120)
    role: UserRole
    phone: str | None = Field(default=None, max_length=40)
    company: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)


class RegisterStartRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=120)
    role: UserRole
    phone: str = Field(min_length=7, max_length=40)
    company: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    """Legacy password login (kept for compatibility). Prefer OTP login flow."""

    email: EmailStr
    password: str


class LoginStartRequest(BaseModel):
    email: EmailStr


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)
    purpose: OtpPurpose


class OtpStartResponse(BaseModel):
    message: str
    email: EmailStr
    purpose: OtpPurpose
    expires_in_minutes: int = 10


class AuthResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    token: str
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    email_verified: bool = False


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    company: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)


class HealthResponse(BaseModel):
    status: str
    application: str
    timestamp: str


class MessageResponse(BaseModel):
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
