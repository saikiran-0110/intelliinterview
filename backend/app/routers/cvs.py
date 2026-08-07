from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.analysis_schemas import CandidateCvResponse, to_cv_response
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import CandidateCv, User, UserRole
from app.services.document_parser import DocumentParserService
from app.services.skill_catalog import parse_cv_profile

router = APIRouter(prefix="/api/cvs", tags=["cvs"])
document_parser = DocumentParserService()


def _accessible_cv(db: Session, cv_id: UUID, current_user: User) -> CandidateCv:
    cv = db.get(CandidateCv, cv_id)
    if cv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    if current_user.role == UserRole.RECRUITER:
        # Recruiters can access CVs they uploaded or CVs attached to their applications.
        if cv.uploaded_by == current_user.id:
            return cv
        from app.models import JobApplication

        linked = (
            db.query(JobApplication)
            .filter(JobApplication.cv_id == cv.id, JobApplication.recruiter_id == current_user.id)
            .first()
        )
        if linked:
            return cv
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    if current_user.role == UserRole.CANDIDATE and cv.uploaded_by == current_user.id:
        return cv
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")


@router.get("", response_model=list[CandidateCvResponse])
def list_cvs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
) -> CandidateCvResponse:
    return to_cv_response(_accessible_cv(db, cv_id, current_user))


@router.get("/{cv_id}/download")
def download_cv(
    cv_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    cv = _accessible_cv(db, cv_id, current_user)
    if cv.file_data:
        return Response(
            content=cv.file_data,
            media_type=cv.content_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{cv.original_filename}"'},
        )
    # Fallback: export extracted text when original bytes are unavailable.
    text = cv.extracted_text or ""
    return Response(
        content=text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{cv.original_filename}.txt"'},
    )


@router.post("/upload", response_model=CandidateCvResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    candidate_name: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    name = (candidate_name or current_user.full_name).strip()
    parsed_profile = parse_cv_profile(extracted_text)
    cv = CandidateCv(
        candidate_name=name,
        original_filename=file.filename,
        extracted_text=extracted_text,
        parsed_profile=parsed_profile,
        file_data=file_bytes,
        content_type=file.content_type,
        uploaded_by=current_user.id,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return to_cv_response(cv)
