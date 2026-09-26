from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import NotificationChannel, ScheduleConfirmationStatus


class SlotSuggestionResponse(BaseModel):
    id: UUID
    session_id: UUID
    starts_at: datetime
    ends_at: datetime
    is_selected: bool
    created_at: datetime


class ProposeSlotsRequest(BaseModel):
    session_id: UUID
    duration_minutes: int = Field(default=45, ge=15, le=180)
    slot_count: int = Field(default=5, ge=1, le=10)
    timezone: str = "UTC"


class ConfirmSlotRequest(BaseModel):
    slot_id: UUID
    candidate_note: str | None = None


class RescheduleRequest(BaseModel):
    candidate_note: str | None = None


class CandidateMessageRequest(BaseModel):
    candidate_note: str = Field(min_length=1, max_length=2000)


class RecruiterForceScheduleRequest(BaseModel):
    """Demo/admin override: set confirmed interview time without candidate approval."""

    starts_at: datetime | None = None
    duration_minutes: int = Field(default=45, ge=15, le=180)
    notify_candidate: bool = True


class ScheduleItemResponse(BaseModel):
    session_id: UUID
    candidate_name: str
    candidate_email: str
    job_title: str
    confirmation_status: ScheduleConfirmationStatus
    scheduled_at: datetime | None
    duration_minutes: int
    timezone: str
    candidate_note: str | None
    slots: list[SlotSuggestionResponse]


class CalendarLinksResponse(BaseModel):
    google_url: str
    outlook_url: str
    ics_url: str


class NotificationResponse(BaseModel):
    id: UUID
    title: str
    body: str
    link: str | None
    channel: NotificationChannel
    is_read: bool
    email_sent: bool
    related_session_id: UUID | None
    created_at: datetime
