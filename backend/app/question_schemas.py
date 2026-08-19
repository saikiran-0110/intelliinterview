from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import QuestionSource


class QuestionGenerateRequest(BaseModel):
    gap_analysis_id: UUID


class CustomQuestionRequest(BaseModel):
    plan_id: UUID
    text: str = Field(min_length=5, max_length=2000)
    topic: str = Field(default="custom", min_length=1, max_length=120)
    skill_ref: str | None = None


class QuestionUpdateRequest(BaseModel):
    text: str | None = Field(default=None, min_length=5, max_length=2000)
    topic: str | None = Field(default=None, min_length=1, max_length=120)
    approved: bool | None = None
    skill_ref: str | None = None
    rationale: str | None = None


class QuestionReorderRequest(BaseModel):
    question_ids: list[UUID] = Field(min_length=1)


class InterviewQuestionResponse(BaseModel):
    id: UUID
    plan_id: UUID
    text: str
    topic: str
    question_type: str
    source: QuestionSource
    skill_ref: str | None
    rationale: str | None
    sort_order: int
    approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionPlanResponse(BaseModel):
    id: UUID
    gap_analysis_id: UUID
    title: str
    candidate_name: str
    candidate_email: str | None = None
    job_title: str
    job_spec_id: UUID | None = None
    cv_id: UUID | None = None
    questions: list[InterviewQuestionResponse]
    ai_question_count: int
    recruiter_question_count: int
    approved_count: int
    created_at: datetime
    updated_at: datetime


def to_question_response(question: Any) -> InterviewQuestionResponse:
    return InterviewQuestionResponse(
        id=question.id,
        plan_id=question.plan_id,
        text=question.text,
        topic=question.topic,
        question_type=question.question_type,
        source=question.source,
        skill_ref=question.skill_ref,
        rationale=question.rationale,
        sort_order=question.sort_order,
        approved=question.approved,
        created_at=question.created_at,
    )


def to_plan_response(
    plan: Any,
    questions: list[Any],
    candidate_name: str,
    job_title: str,
    *,
    candidate_email: str | None = None,
    job_spec_id: UUID | None = None,
    cv_id: UUID | None = None,
) -> QuestionPlanResponse:
    ordered = sorted(questions, key=lambda item: item.sort_order)
    ai_count = sum(1 for item in ordered if item.source == QuestionSource.AI)
    recruiter_count = sum(1 for item in ordered if item.source == QuestionSource.RECRUITER)
    approved_count = sum(1 for item in ordered if item.approved)
    return QuestionPlanResponse(
        id=plan.id,
        gap_analysis_id=plan.gap_analysis_id,
        title=plan.title,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        job_title=job_title,
        job_spec_id=job_spec_id,
        cv_id=cv_id,
        questions=[to_question_response(item) for item in ordered],
        ai_question_count=ai_count,
        recruiter_question_count=recruiter_count,
        approved_count=approved_count,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
