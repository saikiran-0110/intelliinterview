from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.email_types import FlexibleEmail
from app.models import PipelineStage


class ApplicationCreateRequest(BaseModel):
    job_spec_id: UUID
    cv_id: UUID | None = None
    contact_full_name: str = Field(min_length=1, max_length=120)
    contact_email: FlexibleEmail
    contact_phone: str = Field(min_length=7, max_length=40)
    contact_linkedin: str | None = Field(default=None, max_length=255)
    current_location: str | None = Field(default=None, max_length=255)
    expected_salary_gbp: float | None = Field(default=None, ge=0)
    right_to_work_uk: bool = True
    cover_note: str | None = Field(default=None, max_length=4000)


class MatchPreviewRequest(BaseModel):
    job_spec_id: UUID
    cv_id: UUID | None = None


class MatchPreviewResponse(BaseModel):
    job_spec_id: UUID
    job_title: str
    cv_id: UUID
    match_score: float
    strong_matches: list[str] = Field(default_factory=list)
    partial_matches: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    plain_language_breakdown: str
    narrative_summary: str


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
    contact_full_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_linkedin: str | None = None
    current_location: str | None = None
    expected_salary_gbp: float | None = None
    right_to_work_uk: bool | None = None
    cover_note: str | None = None
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


class PreparationProgressUpdateRequest(BaseModel):
    item_id: str = Field(min_length=1, max_length=120)
    completed: bool = True


class PreparationQuestionItem(BaseModel):
    id: str
    question: str
    difficulty: str = "intermediate"
    topic: str = "general"
    talking_points: list[str] = Field(default_factory=list)
    technical_context: str = ""


class PreparationStudyModule(BaseModel):
    id: str
    title: str
    summary: str
    technical_details: str
    topic: str = "general"
    estimated_minutes: int = 30


class PreparationChecklistItem(BaseModel):
    id: str
    label: str
    category: str = "practice"
    technical_hint: str = ""


class PreparationPackResponse(BaseModel):
    id: UUID
    job_spec_id: UUID
    job_title: str
    cv_id: UUID
    practice_questions: list[PreparationQuestionItem]
    guidance: str
    focus_areas: list[str]
    study_modules: list[PreparationStudyModule] = Field(default_factory=list)
    checklist_items: list[PreparationChecklistItem] = Field(default_factory=list)
    completed_item_ids: list[str] = Field(default_factory=list)
    progress_percent: int = 0
    model_version: str | None
    created_at: datetime


class AssistantQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AssistantQueryResponse(BaseModel):
    answer: str
    structured: dict
    tools_used: list[str]


class NextActionItem(BaseModel):
    id: str
    priority: int
    title: str
    detail: str
    cta_label: str | None = None
    cta_path: str | None = None


class NextActionsResponse(BaseModel):
    items: list[NextActionItem]
    generated_from: str = "pipeline-rules"
