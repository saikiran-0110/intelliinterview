from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, JobSpecification, User, UserRole
from app.optional_schemas import (
    PreparationChecklistItem,
    PreparationGenerateRequest,
    PreparationPackResponse,
    PreparationProgressUpdateRequest,
    PreparationQuestionItem,
    PreparationStudyModule,
)
from app.services.preparation import PreparationService, _normalize_questions

router = APIRouter(prefix="/api/preparation", tags=["preparation"])
prep_service = PreparationService()


def _to_response(db: Session, pack) -> PreparationPackResponse:
    job = db.get(JobSpecification, pack.job_spec_id)
    questions = [
        PreparationQuestionItem(**item) for item in _normalize_questions(pack.practice_questions or [])
    ]
    modules = []
    for item in pack.study_modules or []:
        if not isinstance(item, dict):
            continue
        modules.append(
            PreparationStudyModule(
                id=str(item.get("id") or ""),
                title=str(item.get("title") or "Study module"),
                summary=str(item.get("summary") or ""),
                technical_details=str(item.get("technical_details") or ""),
                topic=str(item.get("topic") or "general"),
                estimated_minutes=int(item.get("estimated_minutes") or 30),
            )
        )
    checklist = []
    for item in pack.checklist_items or []:
        if not isinstance(item, dict):
            continue
        checklist.append(
            PreparationChecklistItem(
                id=str(item.get("id") or ""),
                label=str(item.get("label") or ""),
                category=str(item.get("category") or "practice"),
                technical_hint=str(item.get("technical_hint") or ""),
            )
        )
    completed = [str(value) for value in (pack.completed_item_ids or [])]
    trackable = [item.id for item in questions] + [item.id for item in modules] + [item.id for item in checklist]
    trackable = [item_id for item_id in trackable if item_id]
    done = len([item_id for item_id in completed if item_id in trackable])
    progress = int(round((done / len(trackable)) * 100)) if trackable else 0
    return PreparationPackResponse(
        id=pack.id,
        job_spec_id=pack.job_spec_id,
        job_title=job.title if job else "Role",
        cv_id=pack.cv_id,
        practice_questions=questions,
        guidance=pack.guidance,
        focus_areas=pack.focus_areas or [],
        study_modules=modules,
        checklist_items=checklist,
        completed_item_ids=completed,
        progress_percent=progress,
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


@router.patch("/{pack_id}/progress", response_model=PreparationPackResponse)
def update_preparation_progress(
    pack_id: UUID,
    request: PreparationProgressUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> PreparationPackResponse:
    pack = prep_service.get_owned(db, pack_id, current_user.id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preparation pack not found")
    updated = prep_service.toggle_progress(
        db,
        pack,
        item_id=request.item_id.strip(),
        completed=request.completed,
    )
    return _to_response(db, updated)


@router.delete("/{pack_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preparation_pack(
    pack_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> None:
    pack = prep_service.get_owned(db, pack_id, current_user.id)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preparation pack not found")
    prep_service.delete_pack(db, pack)
