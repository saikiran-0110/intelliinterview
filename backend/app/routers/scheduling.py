from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    GapAnalysis,
    InterviewSession,
    InterviewSlotSuggestion,
    JobSpecification,
    Notification,
    User,
    UserRole,
)
from app.scheduling_schemas import (
    CandidateMessageRequest,
    ConfirmSlotRequest,
    NotificationResponse,
    ProposeSlotsRequest,
    RescheduleRequest,
    ScheduleItemResponse,
    SlotSuggestionResponse,
)
from app.services.notifications import NotificationService
from app.services.scheduling import SchedulingService

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])
scheduling = SchedulingService()
notifications = NotificationService()


def _slot_response(slot: InterviewSlotSuggestion) -> SlotSuggestionResponse:
    return SlotSuggestionResponse(
        id=slot.id,
        session_id=slot.session_id,
        starts_at=slot.starts_at,
        ends_at=slot.ends_at,
        is_selected=slot.is_selected,
        created_at=slot.created_at,
    )


def _schedule_item(db: Session, session: InterviewSession) -> ScheduleItemResponse:
    candidate = db.get(User, session.candidate_user_id)
    job = db.get(JobSpecification, session.job_spec_id)
    slots = (
        db.query(InterviewSlotSuggestion)
        .filter(InterviewSlotSuggestion.session_id == session.id)
        .order_by(InterviewSlotSuggestion.starts_at.asc())
        .all()
    )
    return ScheduleItemResponse(
        session_id=session.id,
        candidate_name=candidate.full_name if candidate else "Candidate",
        candidate_email=candidate.email if candidate else "",
        job_title=job.title if job else "Role",
        confirmation_status=session.confirmation_status,
        scheduled_at=session.scheduled_at,
        duration_minutes=session.duration_minutes,
        timezone=session.timezone,
        candidate_note=session.candidate_note,
        slots=[_slot_response(slot) for slot in slots],
    )


def _notification_response(item: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=item.id,
        title=item.title,
        body=item.body,
        link=item.link,
        channel=item.channel,
        is_read=item.is_read,
        email_sent=item.email_sent,
        related_session_id=item.related_session_id,
        created_at=item.created_at,
    )


@router.get("/sessions", response_model=list[ScheduleItemResponse])
def list_schedule_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ScheduleItemResponse]:
    query = db.query(InterviewSession)
    if current_user.role == UserRole.RECRUITER:
        query = query.filter(InterviewSession.recruiter_id == current_user.id)
    elif current_user.role == UserRole.CANDIDATE:
        query = query.filter(InterviewSession.candidate_user_id == current_user.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    sessions = query.order_by(InterviewSession.created_at.desc()).all()
    return [_schedule_item(db, session) for session in sessions]


@router.post("/propose", response_model=ScheduleItemResponse, status_code=status.HTTP_201_CREATED)
def propose_slots(
    request: ProposeSlotsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> ScheduleItemResponse:
    session = db.get(InterviewSession, request.session_id)
    if session is None or session.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.duration_minutes = request.duration_minutes
    session.timezone = request.timezone
    db.add(session)

    # Clear previous unselected proposals when recruiter regenerates slots.
    db.query(InterviewSlotSuggestion).filter(InterviewSlotSuggestion.session_id == session.id).delete()
    db.commit()

    slot_times = scheduling.suggest_slots(count=request.slot_count, duration_minutes=request.duration_minutes)
    scheduling.attach_slots(db, session, current_user.id, slot_times)

    gap = db.get(GapAnalysis, session.gap_analysis_id)
    scheduling.ensure_application_for_session(db, session, gap.match_score if gap else None)
    scheduling.notify_candidate_of_slots(db, session)
    return _schedule_item(db, session)


@router.post("/{session_id}/confirm", response_model=ScheduleItemResponse)
def confirm_slot(
    session_id: UUID,
    request: ConfirmSlotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> ScheduleItemResponse:
    session = db.get(InterviewSession, session_id)
    if session is None or session.candidate_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    try:
        scheduling.confirm_slot(db, session, request.slot_id, request.candidate_note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _schedule_item(db, session)


@router.post("/{session_id}/reschedule", response_model=ScheduleItemResponse)
def request_reschedule(
    session_id: UUID,
    request: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> ScheduleItemResponse:
    session = db.get(InterviewSession, session_id)
    if session is None or session.candidate_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    scheduling.request_reschedule(db, session, request.candidate_note)
    return _schedule_item(db, session)


@router.post("/{session_id}/message", response_model=ScheduleItemResponse)
def send_candidate_message(
    session_id: UUID,
    request: CandidateMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> ScheduleItemResponse:
    session = db.get(InterviewSession, session_id)
    if session is None or session.candidate_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    try:
        scheduling.send_candidate_message(db, session, request.candidate_note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _schedule_item(db, session)


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationResponse]:
    items = notifications.list_for_user(db, current_user.id)
    return [_notification_response(item) for item in items]


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    item = db.get(Notification, notification_id)
    if item is None or item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notifications.mark_read(db, item)
    return _notification_response(item)
