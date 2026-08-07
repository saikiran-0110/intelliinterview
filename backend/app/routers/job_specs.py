from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import JobSpecification, User, UserRole
from app.analysis_schemas import (
    JobSpecificationCreateRequest,
    JobSpecificationResponse,
    to_job_spec_response,
)
from app.services.document_parser import DocumentParserService
from app.services.skill_catalog import parse_job_requirements
from pydantic import BaseModel

router = APIRouter(prefix="/api/job-specs", tags=["job-specs"])
document_parser = DocumentParserService()


class JobSpecVisibilityRequest(BaseModel):
    is_open: bool


@router.get("", response_model=list[JobSpecificationResponse])
def list_job_specs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> list[JobSpecificationResponse]:
    specs = (
        db.query(JobSpecification)
        .filter(JobSpecification.created_by == current_user.id)
        .order_by(JobSpecification.created_at.desc())
        .all()
    )
    return [to_job_spec_response(spec) for spec in specs]


@router.get("/open", response_model=list[JobSpecificationResponse])
def list_open_job_specs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobSpecificationResponse]:
    specs = (
        db.query(JobSpecification)
        .filter(JobSpecification.is_open.is_(True))
        .order_by(JobSpecification.created_at.desc())
        .all()
    )
    return [to_job_spec_response(spec) for spec in specs]


@router.get("/{job_spec_id}", response_model=JobSpecificationResponse)
def get_job_spec(
    job_spec_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> JobSpecificationResponse:
    job_spec = db.get(JobSpecification, job_spec_id)
    if job_spec is None or job_spec.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job specification not found")
    return to_job_spec_response(job_spec)


@router.post("", response_model=JobSpecificationResponse, status_code=status.HTTP_201_CREATED)
def create_job_spec(
    request: JobSpecificationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> JobSpecificationResponse:
    parsed_requirements = parse_job_requirements(request.description)
    job_spec = JobSpecification(
        title=request.title.strip(),
        description=request.description.strip(),
        extracted_text=request.description.strip(),
        parsed_requirements=parsed_requirements,
        is_open=request.is_open,
        created_by=current_user.id,
    )
    db.add(job_spec)
    db.commit()
    db.refresh(job_spec)
    return to_job_spec_response(job_spec)


@router.post("/upload", response_model=JobSpecificationResponse, status_code=status.HTTP_201_CREATED)
async def upload_job_spec(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> JobSpecificationResponse:
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
            detail=f"Failed to parse job specification: {exc}",
        ) from exc

    parsed_requirements = parse_job_requirements(extracted_text)
    job_spec = JobSpecification(
        title=title.strip(),
        description=extracted_text,
        extracted_text=extracted_text,
        parsed_requirements=parsed_requirements,
        is_open=True,
        created_by=current_user.id,
    )
    db.add(job_spec)
    db.commit()
    db.refresh(job_spec)
    return to_job_spec_response(job_spec)


@router.patch("/{job_spec_id}/visibility", response_model=JobSpecificationResponse)
def set_job_visibility(
    job_spec_id: UUID,
    request: JobSpecVisibilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> JobSpecificationResponse:
    job_spec = db.get(JobSpecification, job_spec_id)
    if job_spec is None or job_spec.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job specification not found")
    job_spec.is_open = request.is_open
    db.add(job_spec)
    db.commit()
    db.refresh(job_spec)
    return to_job_spec_response(job_spec)
