from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import require_role
from app.models import JobSpecification, User, UserRole
from app.analysis_schemas import (
    JobSpecificationCreateRequest,
    JobSpecificationResponse,
    to_job_spec_response,
)
from app.services.document_parser import DocumentParserService
from app.services.skill_catalog import parse_job_requirements

router = APIRouter(prefix="/api/job-specs", tags=["job-specs"])
document_parser = DocumentParserService()


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

    parsed_requirements = parse_job_requirements(extracted_text)
    job_spec = JobSpecification(
        title=title.strip(),
        description=extracted_text,
        extracted_text=extracted_text,
        parsed_requirements=parsed_requirements,
        created_by=current_user.id,
    )
    db.add(job_spec)
    db.commit()
    db.refresh(job_spec)
    return to_job_spec_response(job_spec)
