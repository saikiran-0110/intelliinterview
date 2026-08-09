from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, JobSpecification, User, UserRole
from app.optional_schemas import PreparationGenerateRequest, PreparationPackResponse
from app.services.preparation import PreparationService

router = APIRouter(prefix="/api/preparation", tags=["preparation"])
prep_service = PreparationService()


def _to_response(db: Session, pack) -> PreparationPackResponse:
    job = db.get(JobSpecification, pack.job_spec_id)
    return PreparationPackResponse(
        id=pack.id,
        job_spec_id=pack.job_spec_id,
        job_title=job.title if job else "Role",
        cv_id=pack.cv_id,
        practice_questions=pack.practice_questions or [],
        guidance=pack.guidance,
        focus_areas=pack.focus_areas or [],
        model_version=pack.model_version,
        created_at=pack.created_at,
    )


@router.get("/me", response_model=list[PreparationPackResponse])
def list_my_preparation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> list[PreparationPackResponse]:
    packs = prep_service.list_for_candidate(db, current_user.id)
    return [_to_response(db, pack) for pack in packs]


@router.post("/generate", response_model=PreparationPackResponse, status_code=status.HTTP_201_CREATED)
def generate_preparation(
    request: PreparationGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> PreparationPackResponse:
    job = db.get(JobSpecification, request.job_spec_id)
    if job is None or not job.is_open:
        # Allow prep against recruiter jobs even if closed, if candidate already applied context.
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a CV first")

    pack = prep_service.generate(db, candidate_user_id=current_user.id, cv=cv, job=job)
    return _to_response(db, pack)
