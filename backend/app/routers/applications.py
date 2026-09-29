from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import (
    CandidateCv,
    GapAnalysis,
    InterviewSession,
    InterviewSessionStatus,
    JobApplication,
    JobSpecification,
    PipelineStage,
    User,
    UserRole,
)
from app.optional_schemas import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStageUpdateRequest,
    MatchPreviewRequest,
    MatchPreviewResponse,
)
from app.services.gap_analysis import GapAnalysisService
from app.services.notifications import NotificationService
from app.services.ranking import _plain_language, _skill_names

router = APIRouter(prefix="/api/applications", tags=["applications"])
gap_service = GapAnalysisService()
notifications = NotificationService()


def _to_response(db: Session, app: JobApplication) -> ApplicationResponse:
    job = db.get(JobSpecification, app.job_spec_id)
    candidate = db.get(User, app.candidate_user_id)
    completed_session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.job_spec_id == app.job_spec_id,
            InterviewSession.candidate_user_id == app.candidate_user_id,
            InterviewSession.recruiter_id == app.recruiter_id,
            InterviewSession.status == InterviewSessionStatus.COMPLETED,
        )
        .first()
    )
    return ApplicationResponse(
        id=app.id,
        job_spec_id=app.job_spec_id,
        job_title=job.title if job else "Role",
        candidate_user_id=app.candidate_user_id,
        candidate_name=app.contact_full_name or (candidate.full_name if candidate else "Candidate"),
        candidate_email=app.contact_email or (candidate.email if candidate else ""),
        cv_id=app.cv_id,
        gap_analysis_id=app.gap_analysis_id,
        recruiter_id=app.recruiter_id,
        stage=app.stage,
        match_score=app.match_score,
        notes=app.notes,
        contact_full_name=app.contact_full_name,
        contact_email=app.contact_email,
        contact_phone=app.contact_phone,
        contact_linkedin=app.contact_linkedin,
        current_location=app.current_location,
        expected_salary_gbp=app.expected_salary_gbp,
        right_to_work_uk=app.right_to_work_uk,
        cover_note=app.cover_note,
        has_completed_interview=completed_session is not None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


def _resolve_candidate_cv(db: Session, current_user: User, cv_id: UUID | None) -> CandidateCv:
    if cv_id:
        cv = db.get(CandidateCv, cv_id)
        if cv is None or cv.uploaded_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
        return cv
    cv = (
        db.query(CandidateCv)
        .filter(CandidateCv.uploaded_by == current_user.id)
        .order_by(CandidateCv.created_at.desc())
        .first()
    )
    if cv is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a CV before checking match or applying",
        )
    return cv


@router.get("/me", response_model=list[ApplicationResponse])
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> list[ApplicationResponse]:
    apps = (
        db.query(JobApplication)
        .filter(JobApplication.candidate_user_id == current_user.id)
        .order_by(JobApplication.created_at.desc())
        .all()
    )
    return [_to_response(db, app) for app in apps]


@router.get("", response_model=list[ApplicationResponse])
def list_recruiter_applications(
    job_spec_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[ApplicationResponse]:
    query = db.query(JobApplication).filter(JobApplication.recruiter_id == current_user.id)
    if job_spec_id:
        query = query.filter(JobApplication.job_spec_id == job_spec_id)
    apps = query.order_by(JobApplication.created_at.desc()).all()
    return [_to_response(db, app) for app in apps]


@router.post("/match-preview", response_model=MatchPreviewResponse)
def preview_job_match(
    request: MatchPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> MatchPreviewResponse:
    job = db.get(JobSpecification, request.job_spec_id)
    if job is None or not job.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Open job not found")
    cv = _resolve_candidate_cv(db, current_user, request.cv_id)
    owner_id = job.created_by or current_user.id
    analysis = (
        db.query(GapAnalysis)
        .filter(GapAnalysis.cv_id == cv.id, GapAnalysis.job_spec_id == job.id)
        .order_by(GapAnalysis.created_at.desc())
        .first()
    )
    if analysis is None:
        analysis = gap_service.analyse(db, cv, job, owner_id)
    strong = _skill_names(analysis.strong_matches)
    partial = _skill_names(analysis.partial_matches)
    gaps = _skill_names(analysis.gaps)
    score = float(analysis.match_score or 0)
    return MatchPreviewResponse(
        job_spec_id=job.id,
        job_title=job.title,
        cv_id=cv.id,
        match_score=score,
        strong_matches=strong,
        partial_matches=partial,
        gaps=gaps,
        plain_language_breakdown=_plain_language(score, strong, gaps),
        narrative_summary=analysis.narrative_summary or "",
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_for_job(
    request: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> ApplicationResponse:
    job = db.get(JobSpecification, request.job_spec_id)
    if job is None or not job.is_open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Open job not found")

    existing = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_spec_id == job.id,
            JobApplication.candidate_user_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already applied for this role")

    cv = _resolve_candidate_cv(db, current_user, request.cv_id)

    if job.created_by is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job has no owning recruiter")

    analysis = (
        db.query(GapAnalysis)
        .filter(GapAnalysis.cv_id == cv.id, GapAnalysis.job_spec_id == job.id)
        .order_by(GapAnalysis.created_at.desc())
        .first()
    )
    if analysis is None:
        analysis = gap_service.analyse(db, cv, job, job.created_by)
    application = JobApplication(
        job_spec_id=job.id,
        candidate_user_id=current_user.id,
        cv_id=cv.id,
        gap_analysis_id=analysis.id,
        recruiter_id=job.created_by,
        stage=PipelineStage.APPLIED,
        match_score=analysis.match_score,
        contact_full_name=request.contact_full_name.strip(),
        contact_email=str(request.contact_email).strip().lower(),
        contact_phone=request.contact_phone.strip(),
        contact_linkedin=(request.contact_linkedin or "").strip() or None,
        current_location=(request.current_location or "").strip() or None,
        expected_salary_gbp=request.expected_salary_gbp,
        right_to_work_uk=request.right_to_work_uk,
        cover_note=(request.cover_note or "").strip() or None,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    score_text = f"{application.match_score:.0f}/100" if application.match_score is not None else "n/a"
    notifications.notify(
        db,
        user_id=job.created_by,
        title=f"New application: {job.title}",
        body=(
            f"{application.contact_full_name} applied for {job.title} "
            f"(match {score_text}). Review them on the Hiring Board."
        ),
        link="/recruiter/jobs",
    )
    notifications.notify(
        db,
        user_id=current_user.id,
        title=f"Application submitted: {job.title}",
        body=(
            f"We received your application for {job.title}. "
            f"Current match score: {score_text}. You will be notified when the stage changes."
        ),
        link="/candidate/applications",
    )
    return _to_response(db, application)


@router.patch("/{application_id}/stage", response_model=ApplicationResponse)
def update_application_stage(
    application_id: UUID,
    request: ApplicationStageUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> ApplicationResponse:
    application = db.get(JobApplication, application_id)
    if application is None or application.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    application.stage = request.stage
    if request.notes is not None:
        application.notes = request.notes
    db.add(application)
    db.commit()
    db.refresh(application)

    job = db.get(JobSpecification, application.job_spec_id)
    job_title = job.title if job else "the role"

    decision_copy = {
        PipelineStage.REJECTED: (
            f"Application update: {job_title}",
            f"Thank you for taking the time to interview for {job_title}. After careful "
            "consideration we will not be moving forward with your application on this "
            "occasion. We appreciate the time you invested and wish you every success.",
        ),
        PipelineStage.OFFER: (
            f"You're moving forward: {job_title}",
            f"Great news - you've passed the screening interview for {job_title} and "
            "are moving forward to the next stage of the hiring process. Your recruiter "
            "will be in touch with details shortly.",
        ),
    }

    if request.stage in decision_copy:
        title, body = decision_copy[request.stage]
        if request.notes:
            body += f"\n\nMessage from the recruiter: {request.notes}"
    else:
        title = f"Application update: {job_title}"
        body = (
            f"Your application for {job_title} moved to {request.stage.value.replace('_', ' ').title()}."
            + (f" Note: {request.notes}" if request.notes else "")
        )
        if request.stage == PipelineStage.SHORTLISTED:
            body += " Your recruiter will prepare interview questions and propose a time slot next."

    notifications.notify(
        db,
        user_id=application.candidate_user_id,
        title=title,
        body=body,
        link="/candidate/applications",
    )
    return _to_response(db, application)
