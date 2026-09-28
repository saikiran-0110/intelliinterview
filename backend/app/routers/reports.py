from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import (
    InterviewReport,
    InterviewSession,
    InterviewSessionStatus,
    JobApplication,
    JobSpecification,
    QuestionPlan,
    User,
    UserRole,
)
from app.report_schemas import EvidenceItem, InterviewReportResponse, InterviewReportSummary
from app.services.report_generation import ReportGenerationService

router = APIRouter(prefix="/api/reports", tags=["reports"])
report_service = ReportGenerationService()


def _to_response(db: Session, report: InterviewReport) -> InterviewReportResponse:
    candidate = db.get(User, report.candidate_user_id)
    job_spec = db.get(JobSpecification, report.job_spec_id)
    session = db.get(InterviewSession, report.session_id)
    plan = db.get(QuestionPlan, session.question_plan_id) if session else None

    evidence = []
    for item in report.evidence_items or []:
        if isinstance(item, dict):
            evidence.append(EvidenceItem(**item))

    application = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_spec_id == report.job_spec_id,
            JobApplication.candidate_user_id == report.candidate_user_id,
            JobApplication.recruiter_id == report.recruiter_id,
        )
        .first()
    )

    return InterviewReportResponse(
        id=report.id,
        session_id=report.session_id,
        candidate_name=candidate.full_name if candidate else "Candidate",
        candidate_email=candidate.email if candidate else "",
        job_title=job_spec.title if job_spec else "Role",
        plan_title=plan.title if plan else "Interview plan",
        technical_fit_score=report.technical_fit_score,
        communication_score=report.communication_score,
        problem_solving_score=report.problem_solving_score,
        role_alignment_score=report.role_alignment_score,
        overall_score=report.overall_score,
        recommendation=report.recommendation,
        recommendation_summary=report.recommendation_summary,
        strengths=report.strengths or [],
        weaknesses=report.weaknesses or [],
        evidence_items=evidence,
        dimension_notes=report.dimension_notes,
        model_version=report.model_version,
        generated_at=report.generated_at,
        created_at=report.created_at,
        application_id=application.id if application else None,
        application_stage=application.stage if application else None,
        candidate_user_id=report.candidate_user_id,
        candidate_has_photo=bool(candidate and getattr(candidate, "profile_photo", None)),
    )


def _to_summary(db: Session, report: InterviewReport) -> InterviewReportSummary:
    candidate = db.get(User, report.candidate_user_id)
    job_spec = db.get(JobSpecification, report.job_spec_id)
    return InterviewReportSummary(
        id=report.id,
        session_id=report.session_id,
        candidate_name=candidate.full_name if candidate else "Candidate",
        job_title=job_spec.title if job_spec else "Role",
        overall_score=report.overall_score,
        recommendation=report.recommendation,
        technical_fit_score=report.technical_fit_score,
        communication_score=report.communication_score,
        problem_solving_score=report.problem_solving_score,
        role_alignment_score=report.role_alignment_score,
        generated_at=report.generated_at,
    )


@router.get("", response_model=list[InterviewReportSummary])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[InterviewReportSummary]:
    reports = (
        db.query(InterviewReport)
        .filter(InterviewReport.recruiter_id == current_user.id)
        .order_by(InterviewReport.generated_at.desc())
        .all()
    )
    return [_to_summary(db, report) for report in reports]


@router.get("/by-session/{session_id}", response_model=InterviewReportResponse)
def get_report_by_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewReportResponse:
    report = (
        db.query(InterviewReport)
        .filter(InterviewReport.session_id == session_id, InterviewReport.recruiter_id == current_user.id)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _to_response(db, report)


@router.post("/generate/{session_id}", response_model=InterviewReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewReportResponse:
    session = db.get(InterviewSession, session_id)
    if session is None or session.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != InterviewSessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report can only be generated for completed sessions",
        )

    report = report_service.generate_for_session(db, session)
    from app.services.notifications import NotificationService

    NotificationService().notify(
        db,
        user_id=current_user.id,
        title="Evaluation report ready",
        body=f"An evaluation report is ready for session {session_id}.",
        link=f"/recruiter/reports",
        related_session_id=session.id,
    )
    if session.candidate_user_id:
        NotificationService().notify(
            db,
            user_id=session.candidate_user_id,
            title="Interview evaluation completed",
            body="Your interview evaluation is complete. Feedback may now be available in your portal.",
            link="/candidate/feedback",
            related_session_id=session.id,
        )
    return _to_response(db, report)


@router.get("/{report_id}", response_model=InterviewReportResponse)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewReportResponse:
    report = db.get(InterviewReport, report_id)
    if report is None or report.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _to_response(db, report)
