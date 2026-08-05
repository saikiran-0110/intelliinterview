from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.feedback_schemas import CandidateFeedbackResponse, CandidateFeedbackSummary
from app.models import CandidateFeedback, InterviewReport, InterviewSession, JobSpecification, User, UserRole
from app.services.candidate_feedback import CandidateFeedbackService

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
feedback_service = CandidateFeedbackService()


def _to_response(db: Session, feedback: CandidateFeedback) -> CandidateFeedbackResponse:
    session = db.get(InterviewSession, feedback.session_id)
    job = db.get(JobSpecification, session.job_spec_id) if session else None
    return CandidateFeedbackResponse(
        id=feedback.id,
        session_id=feedback.session_id,
        job_title=job.title if job else "Role",
        summary=feedback.summary,
        strong_answers=feedback.strong_answers or [],
        improvement_areas=feedback.improvement_areas or [],
        focus_tips=feedback.focus_tips or [],
        model_version=feedback.model_version,
        created_at=feedback.created_at,
    )


@router.get("/me", response_model=list[CandidateFeedbackSummary])
def list_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> list[CandidateFeedbackSummary]:
    items = feedback_service.list_for_candidate(db, current_user.id)
    result: list[CandidateFeedbackSummary] = []
    for item in items:
        session = db.get(InterviewSession, item.session_id)
        job = db.get(JobSpecification, session.job_spec_id) if session else None
        result.append(
            CandidateFeedbackSummary(
                id=item.id,
                session_id=item.session_id,
                job_title=job.title if job else "Role",
                summary=item.summary,
                created_at=item.created_at,
            )
        )
    return result


@router.get("/by-session/{session_id}", response_model=CandidateFeedbackResponse)
def get_feedback_by_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> CandidateFeedbackResponse:
    feedback = feedback_service.get_for_session(db, session_id, current_user.id)
    if feedback is None:
        # Lazy-generate from completed report if available.
        report = (
            db.query(InterviewReport)
            .filter(
                InterviewReport.session_id == session_id,
                InterviewReport.candidate_user_id == current_user.id,
            )
            .first()
        )
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
        feedback = feedback_service.generate_for_report(db, report)
    return _to_response(db, feedback)


@router.post("/generate/{session_id}", response_model=CandidateFeedbackResponse, status_code=status.HTTP_201_CREATED)
def generate_feedback(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> CandidateFeedbackResponse:
    report = (
        db.query(InterviewReport)
        .filter(
            InterviewReport.session_id == session_id,
            InterviewReport.candidate_user_id == current_user.id,
        )
        .first()
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Completed interview report not found for feedback generation",
        )
    feedback = feedback_service.generate_for_report(db, report)
    return _to_response(db, feedback)
