from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, GapAnalysis, JobApplication, JobSpecification, PipelineStage, User, UserRole
from app.optional_schemas import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStageUpdateRequest,
    MatchPreviewRequest,
    MatchPreviewResponse,
)
from app.services.gap_analysis import GapAnalysisService
from app.services.ranking import _plain_language, _skill_names

router = APIRouter(prefix="/api/applications", tags=["applications"])
gap_service = GapAnalysisService()


def _to_response(db: Session, app: JobApplication) -> ApplicationResponse:
    job = db.get(JobSpecification, app.job_spec_id)
    candidate = db.get(User, app.candidate_user_id)
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
    return _to_response(db, application)
