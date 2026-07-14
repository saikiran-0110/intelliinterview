from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, GapAnalysis, InterviewQuestion, JobSpecification, QuestionPlan, User, UserRole
from app.question_schemas import (
    CustomQuestionRequest,
    QuestionGenerateRequest,
    QuestionPlanResponse,
    QuestionReorderRequest,
    QuestionUpdateRequest,
    InterviewQuestionResponse,
    to_plan_response,
    to_question_response,
)
from app.services.question_generation import QuestionGenerationService

router = APIRouter(prefix="/api/questions", tags=["questions"])
question_service = QuestionGenerationService()


def _get_owned_analysis(db: Session, analysis_id: UUID, user: User) -> GapAnalysis:
    analysis = db.get(GapAnalysis, analysis_id)
    if analysis is None or analysis.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap analysis not found")
    return analysis


def _get_owned_plan(db: Session, plan_id: UUID, user: User) -> QuestionPlan:
    plan = db.get(QuestionPlan, plan_id)
    if plan is None or plan.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question plan not found")
    return plan


def _plan_with_context(db: Session, plan: QuestionPlan) -> QuestionPlanResponse:
    analysis = db.get(GapAnalysis, plan.gap_analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked gap analysis not found")
    cv = db.get(CandidateCv, analysis.cv_id)
    job_spec = db.get(JobSpecification, analysis.job_spec_id)
    if cv is None or job_spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked documents not found")
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.plan_id == plan.id)
        .order_by(InterviewQuestion.sort_order.asc())
        .all()
    )
    return to_plan_response(plan, questions, cv.candidate_name, job_spec.title)


@router.post("/generate", response_model=QuestionPlanResponse, status_code=status.HTTP_201_CREATED)
def generate_questions(
    request: QuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> QuestionPlanResponse:
    analysis = _get_owned_analysis(db, request.gap_analysis_id, current_user)
    cv = db.get(CandidateCv, analysis.cv_id)
    job_spec = db.get(JobSpecification, analysis.job_spec_id)
    if cv is None or job_spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked documents not found")

    plan, _questions = question_service.generate_plan(db, analysis, cv, job_spec, current_user.id)
    return _plan_with_context(db, plan)


@router.get("/plans", response_model=list[QuestionPlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[QuestionPlanResponse]:
    plans = (
        db.query(QuestionPlan)
        .filter(QuestionPlan.created_by == current_user.id)
        .order_by(QuestionPlan.created_at.desc())
        .all()
    )
    return [_plan_with_context(db, plan) for plan in plans]


@router.get("/plans/by-analysis/{analysis_id}", response_model=QuestionPlanResponse)
def get_plan_by_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> QuestionPlanResponse:
    _get_owned_analysis(db, analysis_id, current_user)
    plan = (
        db.query(QuestionPlan)
        .filter(QuestionPlan.gap_analysis_id == analysis_id, QuestionPlan.created_by == current_user.id)
        .order_by(QuestionPlan.created_at.desc())
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question plan not found")
    return _plan_with_context(db, plan)


@router.get("/plans/{plan_id}", response_model=QuestionPlanResponse)
def get_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> QuestionPlanResponse:
    plan = _get_owned_plan(db, plan_id, current_user)
    return _plan_with_context(db, plan)


@router.post("/custom", response_model=InterviewQuestionResponse, status_code=status.HTTP_201_CREATED)
def add_custom_question(
    request: CustomQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewQuestionResponse:
    plan = _get_owned_plan(db, request.plan_id, current_user)
    question = question_service.add_custom_question(
        db,
        plan,
        text=request.text,
        topic=request.topic,
        skill_ref=request.skill_ref,
    )
    return to_question_response(question)


@router.patch("/{question_id}", response_model=InterviewQuestionResponse)
def update_question(
    question_id: UUID,
    request: QuestionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewQuestionResponse:
    question = db.get(InterviewQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    plan = _get_owned_plan(db, question.plan_id, current_user)

    if request.text is not None:
        question.text = request.text.strip()
    if request.topic is not None:
        question.topic = request.topic.strip()
    if request.approved is not None:
        question.approved = request.approved
    if request.skill_ref is not None:
        question.skill_ref = request.skill_ref
    if request.rationale is not None:
        question.rationale = request.rationale

    db.add(question)
    db.add(plan)
    db.commit()
    db.refresh(question)
    return to_question_response(question)


@router.put("/plans/{plan_id}/reorder", response_model=QuestionPlanResponse)
def reorder_questions(
    plan_id: UUID,
    request: QuestionReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> QuestionPlanResponse:
    plan = _get_owned_plan(db, plan_id, current_user)
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.plan_id == plan.id)
        .all()
    )
    by_id = {question.id: question for question in questions}
    if set(request.question_ids) != set(by_id.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_ids must include every question in the plan exactly once",
        )

    for index, question_id in enumerate(request.question_ids):
        by_id[question_id].sort_order = index
        db.add(by_id[question_id])

    db.commit()
    return _plan_with_context(db, plan)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> None:
    question = db.get(InterviewQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    _get_owned_plan(db, question.plan_id, current_user)
    db.delete(question)
    db.commit()
