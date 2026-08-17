from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models import EmploymentType, WorkMode


class ParsedProfileResponse(BaseModel):
    skills: list[str] = Field(default_factory=list)
    years_experience: int | None = None
    seniority: str | None = None
    qualifications: list[str] = Field(default_factory=list)


class ParsedRequirementsResponse(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    years_experience_required: int | None = None
    seniority_required: str | None = None
    qualifications_required: list[str] = Field(default_factory=list)


class CandidateCvResponse(BaseModel):
    id: UUID
    candidate_name: str
    original_filename: str
    extracted_text: str | None
    parsed_profile: ParsedProfileResponse | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobSpecificationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    department: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    work_mode: WorkMode = WorkMode.HYBRID
    salary_min_gbp: float | None = Field(default=None, ge=0)
    salary_max_gbp: float | None = Field(default=None, ge=0)
    years_experience_min: int | None = Field(default=None, ge=0, le=50)
    closing_date: date | None = None
    benefits: str | None = None
    is_open: bool = True

    @field_validator("salary_max_gbp")
    @classmethod
    def validate_salary_range(cls, value: float | None, info) -> float | None:
        minimum = info.data.get("salary_min_gbp")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("salary_max_gbp must be greater than or equal to salary_min_gbp")
        return value


class JobSpecificationResponse(BaseModel):
    id: UUID
    title: str
    description: str
    extracted_text: str | None
    parsed_requirements: ParsedRequirementsResponse | None
    department: str | None = None
    location: str | None = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    work_mode: WorkMode = WorkMode.HYBRID
    salary_min_gbp: float | None = None
    salary_max_gbp: float | None = None
    years_experience_min: int | None = None
    closing_date: date | None = None
    benefits: str | None = None
    is_open: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class JobAiDraftRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=4000)


class JobAiDraftResponse(BaseModel):
    title: str
    description: str
    department: str | None = None
    location: str | None = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    work_mode: WorkMode = WorkMode.HYBRID
    salary_min_gbp: float | None = None
    salary_max_gbp: float | None = None
    years_experience_min: int | None = None
    benefits: str | None = None
    model_version: str | None = None


class SkillMatchItem(BaseModel):
    name: str
    category: str = "skill"
    related_cv_skill: str | None = None
    rationale: str | None = None


class EvidencePassage(BaseModel):
    skill: str
    match_type: str
    passage: str


class ExperienceAnalysis(BaseModel):
    alignment: str
    cv_years_experience: int | None = None
    required_years_experience: int | None = None
    cv_seniority: str | None = None
    required_seniority: str | None = None
    notes: list[str] = Field(default_factory=list)


class QualificationsAnalysis(BaseModel):
    alignment: str
    matched_qualifications: list[str] = Field(default_factory=list)
    missing_qualifications: list[str] = Field(default_factory=list)
    additional_qualifications: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class GapAnalysisRequest(BaseModel):
    cv_id: UUID
    job_spec_id: UUID


class GapAnalysisResponse(BaseModel):
    id: UUID
    cv_id: UUID
    job_spec_id: UUID
    candidate_name: str
    job_title: str
    strong_match_count: int
    partial_match_count: int
    gap_count: int
    match_score: float | None
    strong_matches: list[SkillMatchItem]
    partial_matches: list[SkillMatchItem]
    gaps: list[SkillMatchItem]
    experience_analysis: ExperienceAnalysis
    qualifications_analysis: QualificationsAnalysis
    evidence_passages: list[EvidencePassage]
    narrative_summary: str
    created_at: datetime


def to_cv_response(cv: Any) -> CandidateCvResponse:
    profile = None
    if cv.parsed_profile:
        profile = ParsedProfileResponse(**cv.parsed_profile)
    return CandidateCvResponse(
        id=cv.id,
        candidate_name=cv.candidate_name,
        original_filename=cv.original_filename,
        extracted_text=cv.extracted_text,
        parsed_profile=profile,
        created_at=cv.created_at,
    )


def to_job_spec_response(job_spec: Any) -> JobSpecificationResponse:
    requirements = None
    if job_spec.parsed_requirements:
        requirements = ParsedRequirementsResponse(**job_spec.parsed_requirements)
    employment_type = getattr(job_spec, "employment_type", None) or EmploymentType.FULL_TIME
    work_mode = getattr(job_spec, "work_mode", None) or WorkMode.HYBRID
    if isinstance(employment_type, str):
        employment_type = EmploymentType(employment_type)
    if isinstance(work_mode, str):
        work_mode = WorkMode(work_mode)
    return JobSpecificationResponse(
        id=job_spec.id,
        title=job_spec.title,
        description=job_spec.description,
        extracted_text=job_spec.extracted_text,
        parsed_requirements=requirements,
        department=getattr(job_spec, "department", None),
        location=getattr(job_spec, "location", None),
        employment_type=employment_type,
        work_mode=work_mode,
        salary_min_gbp=getattr(job_spec, "salary_min_gbp", None),
        salary_max_gbp=getattr(job_spec, "salary_max_gbp", None),
        years_experience_min=getattr(job_spec, "years_experience_min", None),
        closing_date=getattr(job_spec, "closing_date", None),
        benefits=getattr(job_spec, "benefits", None),
        is_open=bool(getattr(job_spec, "is_open", True)),
        created_at=job_spec.created_at,
    )


def to_gap_analysis_response(analysis: Any, cv: Any, job_spec: Any) -> GapAnalysisResponse:
    return GapAnalysisResponse(
        id=analysis.id,
        cv_id=analysis.cv_id,
        job_spec_id=analysis.job_spec_id,
        candidate_name=cv.candidate_name,
        job_title=job_spec.title,
        strong_match_count=len(analysis.strong_matches),
        partial_match_count=len(analysis.partial_matches),
        gap_count=len(analysis.gaps),
        match_score=analysis.match_score,
        strong_matches=[SkillMatchItem(**item) for item in analysis.strong_matches],
        partial_matches=[SkillMatchItem(**item) for item in analysis.partial_matches],
        gaps=[SkillMatchItem(**item) for item in analysis.gaps],
        experience_analysis=ExperienceAnalysis(**analysis.experience_analysis),
        qualifications_analysis=QualificationsAnalysis(**analysis.qualifications_analysis),
        evidence_passages=[EvidencePassage(**item) for item in analysis.evidence_passages],
        narrative_summary=analysis.narrative_summary,
        created_at=analysis.created_at,
    )
