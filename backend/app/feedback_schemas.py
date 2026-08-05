from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CandidateFeedbackResponse(BaseModel):
    id: UUID
    session_id: UUID
    job_title: str
    summary: str
    strong_answers: list[str]
    improvement_areas: list[str]
    focus_tips: list[str]
    model_version: str | None
    created_at: datetime


class CandidateFeedbackSummary(BaseModel):
    id: UUID
    session_id: UUID
    job_title: str
    summary: str
    created_at: datetime
