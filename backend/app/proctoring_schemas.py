from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models import InterviewSessionStatus, ProctoringEventKind


class ProctoringEventResponse(BaseModel):
    id: UUID
    kind: ProctoringEventKind
    detail: str
    warning_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProctoringCheckResponse(BaseModel):
    violation: bool
    kind: ProctoringEventKind | None
    detail: str
    warning_count: int
    warning_limit: int
    disqualified: bool
    session_status: InterviewSessionStatus
