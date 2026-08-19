from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.email_types import FlexibleEmail
from app.models import InterviewSessionStatus, ScheduleConfirmationStatus, TurnRole


class SessionCreateRequest(BaseModel):
    question_plan_id: UUID
    candidate_email: FlexibleEmail
    follow_up_limit: int = Field(default=1, ge=0, le=3)


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=10000)


class TurnEvaluationResponse(BaseModel):
    technical_score: float | None
    communication_score: float | None
    observations: list[Any]
    evidence_quotes: list[Any]
    strengths: list[Any]
    weaknesses: list[Any]
    should_follow_up: bool
    follow_up_question: str | None
    advance_question: bool
    model_version: str | None


class InterviewTurnResponse(BaseModel):
    id: UUID
    sequence: int
    role: TurnRole
    content: str
    plan_question_id: UUID | None
    is_follow_up: bool
    follow_up_index: int
    created_at: datetime
    evaluation: TurnEvaluationResponse | None = None

    model_config = {"from_attributes": True}


class SessionQuestionProgress(BaseModel):
    index: int
    total: int
    question_id: UUID | None
    question_text: str | None
    topic: str | None


class InterviewSessionResponse(BaseModel):
    id: UUID
    question_plan_id: UUID
    gap_analysis_id: UUID
    cv_id: UUID
    job_spec_id: UUID
    recruiter_id: UUID
    candidate_user_id: UUID
    candidate_name: str
    candidate_email: str
    job_title: str
    plan_title: str
    status: InterviewSessionStatus
    confirmation_status: ScheduleConfirmationStatus
    follow_up_limit: int
    duration_minutes: int = 45
    current_question_index: int
    current_follow_up_count: int
    current_plan_question_id: UUID | None
    progress: SessionQuestionProgress
    turns: list[InterviewTurnResponse]
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class SessionSummaryResponse(BaseModel):
    id: UUID
    status: InterviewSessionStatus
    confirmation_status: ScheduleConfirmationStatus
    candidate_name: str
    candidate_email: str
    job_title: str
    plan_title: str
    current_question_index: int
    total_questions: int
    duration_minutes: int = 45
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    scheduled_at: datetime | None = None
