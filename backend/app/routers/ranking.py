from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import JobSpecification, User, UserRole
from app.optional_schemas import RankedCandidate, RankingResponse
from app.services.ranking import RankingService

router = APIRouter(prefix="/api/ranking", tags=["ranking"])
ranking_service = RankingService()


@router.get("/{job_spec_id}", response_model=RankingResponse)
def rank_candidates_for_job(
    job_spec_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> RankingResponse:
    job = db.get(JobSpecification, job_spec_id)
    if job is None or job.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job specification not found")

    candidates = ranking_service.rank_for_job(db, job, current_user.id)
    return RankingResponse(
        job_spec_id=job.id,
        job_title=job.title,
        candidates=[RankedCandidate(**item) for item in candidates],
    )
