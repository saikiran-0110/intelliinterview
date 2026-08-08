from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import PipelineStage


class ApplicationCreateRequest(BaseModel):
    job_spec_id: UUID
    cv_id: UUID | None = None


class ApplicationStageUpdateRequest(BaseModel):
    stage: PipelineStage
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    job_spec_id: UUID
    job_title: str
    candidate_user_id: UUID
    candidate_name: str
    candidate_email: str
    cv_id: UUID | None
    gap_analysis_id: UUID | None
    recruiter_id: UUID
    stage: PipelineStage
    match_score: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RankedCandidate(BaseModel):
    application_id: UUID | None = None
    candidate_user_id: UUID | None = None
    candidate_name: str
    candidate_email: str | None = None
    cv_id: UUID
    gap_analysis_id: UUID | None = None
    match_score: float
    stage: PipelineStage | None = None
    strong_matches: list[str] = Field(default_factory=list)
    partial_matches: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    narrative_summary: str
    plain_language_breakdown: str


class RankingResponse(BaseModel):
    job_spec_id: UUID
    job_title: str
    candidates: list[RankedCandidate]


class PreparationGenerateRequest(BaseModel):
    job_spec_id: UUID
    cv_id: UUID | None = None


class PreparationPackResponse(BaseModel):
    id: UUID
    job_spec_id: UUID
    job_title: str
    cv_id: UUID
    practice_questions: list[str]
    guidance: str
    focus_areas: list[str]
    model_version: str | None
    created_at: datetime


class AssistantQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AssistantQueryResponse(BaseModel):
    answer: str
    structured: dict
    tools_used: list[str]
