from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, GapAnalysis, JobSpecification, User, UserRole
from app.analysis_schemas import GapAnalysisRequest, GapAnalysisResponse, to_gap_analysis_response
from app.services.gap_analysis import GapAnalysisService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
gap_analysis_service = GapAnalysisService()


@router.get("/gap", response_model=list[GapAnalysisResponse])
def list_gap_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[GapAnalysisResponse]:
    analyses = (
        db.query(GapAnalysis)
        .filter(GapAnalysis.created_by == current_user.id)
        .order_by(GapAnalysis.created_at.desc())
        .all()
    )
    results: list[GapAnalysisResponse] = []
    for analysis in analyses:
        cv = db.get(CandidateCv, analysis.cv_id)
        job_spec = db.get(JobSpecification, analysis.job_spec_id)
        if cv and job_spec:
            results.append(to_gap_analysis_response(analysis, cv, job_spec))
    return results


@router.get("/gap/{analysis_id}", response_model=GapAnalysisResponse)
def get_gap_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> GapAnalysisResponse:
    analysis = db.get(GapAnalysis, analysis_id)
    if analysis is None or analysis.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap analysis not found")

    cv = db.get(CandidateCv, analysis.cv_id)
    job_spec = db.get(JobSpecification, analysis.job_spec_id)
    if cv is None or job_spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked documents not found")

    return to_gap_analysis_response(analysis, cv, job_spec)


@router.post("/gap", response_model=GapAnalysisResponse, status_code=status.HTTP_201_CREATED)
def run_gap_analysis(
    request: GapAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> GapAnalysisResponse:
    cv = db.get(CandidateCv, request.cv_id)
    if cv is None or cv.uploaded_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")

    job_spec = db.get(JobSpecification, request.job_spec_id)
    if job_spec is None or job_spec.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job specification not found")

    if not cv.extracted_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV has no extracted text")

    analysis = gap_analysis_service.analyse(db, cv, job_spec, current_user.id)
    return to_gap_analysis_response(analysis, cv, job_spec)
