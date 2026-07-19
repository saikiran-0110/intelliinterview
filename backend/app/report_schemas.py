from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models import HiringRecommendation


class EvidenceItem(BaseModel):
    turn_id: str
    question_text: str | None = None
    topic: str | None = None
    answer_excerpt: str | None = None
    observations: list[Any] = []
    evidence_quotes: list[Any] = []
    technical_score: float | None = None
    communication_score: float | None = None


class InterviewReportSummary(BaseModel):
    id: UUID
    session_id: UUID
    candidate_name: str
    job_title: str
    overall_score: float
    recommendation: HiringRecommendation
    technical_fit_score: float
    communication_score: float
    problem_solving_score: float
    role_alignment_score: float
    generated_at: datetime


class InterviewReportResponse(BaseModel):
    id: UUID
    session_id: UUID
    candidate_name: str
    candidate_email: str
    job_title: str
    plan_title: str
    technical_fit_score: float
    communication_score: float
    problem_solving_score: float
    role_alignment_score: float
    overall_score: float
    recommendation: HiringRecommendation
    recommendation_summary: str
    strengths: list[str]
    weaknesses: list[str]
    evidence_items: list[EvidenceItem]
    dimension_notes: dict[str, Any] | None
    model_version: str | None
    generated_at: datetime
    created_at: datetime
