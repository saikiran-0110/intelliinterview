from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=120)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    token: str


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)


class HealthResponse(BaseModel):
    status: str
    application: str
    timestamp: str


class MessageResponse(BaseModel):
    message: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
