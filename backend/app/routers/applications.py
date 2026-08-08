from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import CandidateCv, GapAnalysis, JobApplication, JobSpecification, PipelineStage, User, UserRole
from app.optional_schemas import ApplicationCreateRequest, ApplicationResponse, ApplicationStageUpdateRequest
from app.services.gap_analysis import GapAnalysisService

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
        candidate_name=candidate.full_name if candidate else "Candidate",
        candidate_email=candidate.email if candidate else "",
        cv_id=app.cv_id,
        gap_analysis_id=app.gap_analysis_id,
        recruiter_id=app.recruiter_id,
        stage=app.stage,
        match_score=app.match_score,
        notes=app.notes,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


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

    cv: CandidateCv | None = None
    if request.cv_id:
        cv = db.get(CandidateCv, request.cv_id)
        if cv is None or cv.uploaded_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    else:
        cv = (
            db.query(CandidateCv)
            .filter(CandidateCv.uploaded_by == current_user.id)
            .order_by(CandidateCv.created_at.desc())
            .first()
        )
        if cv is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload a CV before applying",
            )

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
