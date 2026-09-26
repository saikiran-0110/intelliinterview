"""Asynchronous candidate interview recording.

Browser MediaRecorder only - no WebRTC, no signalling server; the interviewer is an
AI, so there is no second participant for a live call to connect to. The recording is
for human review only: the AI evaluation reads the typed/transcribed answer text, and
the recording bytes are never sent to any model.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import InterviewRecording, InterviewSession, User, UserRole
from app.recording_schemas import RecordingResponse

router = APIRouter(prefix="/api/sessions", tags=["recordings"])

ALLOWED_CONTENT_TYPES = {"video/webm", "video/mp4", "audio/webm"}


def _get_accessible_session(db: Session, session_id: UUID, user: User) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user.role == UserRole.RECRUITER and session.recruiter_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user.role == UserRole.CANDIDATE and session.candidate_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _get_own_session(db: Session, session_id: UUID, candidate: User) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None or session.candidate_user_id != candidate.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _recording_response(recording: InterviewRecording) -> RecordingResponse:
    return RecordingResponse(
        id=recording.id,
        session_id=recording.session_id,
        content_type=recording.content_type,
        size_bytes=recording.size_bytes,
        duration_seconds=recording.duration_seconds,
        created_at=recording.created_at,
    )


@router.post(
    "/{session_id}/recording",
    response_model=RecordingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_recording(
    session_id: UUID,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> RecordingResponse:
    _get_own_session(db, session_id, current_user)

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {content_type or 'unknown'}",
        )

    file_bytes = await file.read()
    max_bytes = settings.recording_max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Recording exceeds {settings.recording_max_size_mb}MB limit",
        )

    existing = (
        db.query(InterviewRecording).filter(InterviewRecording.session_id == session_id).first()
    )
    if existing:
        existing.content_type = content_type
        existing.size_bytes = len(file_bytes)
        existing.duration_seconds = duration_seconds
        existing.data = file_bytes
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return _recording_response(existing)

    recording = InterviewRecording(
        session_id=session_id,
        content_type=content_type,
        size_bytes=len(file_bytes),
        duration_seconds=duration_seconds,
        data=file_bytes,
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    return _recording_response(recording)


@router.get("/{session_id}/recording")
def get_recording(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    session = _get_accessible_session(db, session_id, current_user)
    recording = (
        db.query(InterviewRecording).filter(InterviewRecording.session_id == session.id).first()
    )
    if recording is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recording for this session")
    return Response(content=recording.data, media_type=recording.content_type)
