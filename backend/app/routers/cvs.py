from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_role
from app.models import CandidateCv, User, UserRole
from app.analysis_schemas import CandidateCvResponse, to_cv_response
from app.services.document_parser import DocumentParserService
from app.services.skill_catalog import parse_cv_profile

router = APIRouter(prefix="/api/cvs", tags=["cvs"])
document_parser = DocumentParserService()


@router.get("", response_model=list[CandidateCvResponse])
def list_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[CandidateCvResponse]:
    cvs = (
        db.query(CandidateCv)
        .filter(CandidateCv.uploaded_by == current_user.id)
        .order_by(CandidateCv.created_at.desc())
        .all()
    )
    return [to_cv_response(cv) for cv in cvs]


@router.get("/{cv_id}", response_model=CandidateCvResponse)
def get_cv(
    cv_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> CandidateCvResponse:
    cv = db.get(CandidateCv, cv_id)
    if cv is None or cv.uploaded_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    return to_cv_response(cv)


@router.post("/upload", response_model=CandidateCvResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    candidate_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> CandidateCvResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    file_bytes = await file.read()
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.upload_max_size_mb}MB limit",
        )

    try:
        extracted_text = document_parser.extract_text(file_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse CV: {exc}",
        ) from exc

    parsed_profile = parse_cv_profile(extracted_text)
    cv = CandidateCv(
        candidate_name=candidate_name.strip(),
        original_filename=file.filename,
        extracted_text=extracted_text,
        parsed_profile=parsed_profile,
        uploaded_by=current_user.id,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return to_cv_response(cv)
