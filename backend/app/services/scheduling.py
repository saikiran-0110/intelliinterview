"""Suggest interview slots and manage confirmation / reschedule flow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    InterviewSession,
    InterviewSlotSuggestion,
    JobApplication,
    JobSpecification,
    PipelineStage,
    ScheduleConfirmationStatus,
    User,
)
from app.services.notifications import NotificationService


class SchedulingService:
    def __init__(self) -> None:
        self.notifications = NotificationService()

    def suggest_slots(
        self,
        *,
        start_from: datetime | None = None,
        count: int = 5,
        duration_minutes: int = 45,
        hour_start: int = 10,
        hour_end: int = 16,
    ) -> list[tuple[datetime, datetime]]:
        """Suggest weekday slots between hour_start and hour_end UTC."""
        cursor = (start_from or datetime.now(timezone.utc)) + timedelta(hours=2)
        # Align to next full hour
        cursor = cursor.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        slots: list[tuple[datetime, datetime]] = []
        guard = 0
        while len(slots) < count and guard < 120:
            guard += 1
            if cursor.weekday() >= 5 or cursor.hour < hour_start or cursor.hour >= hour_end:
                if cursor.weekday() >= 5 or cursor.hour >= hour_end:
                    cursor = (cursor + timedelta(days=1)).replace(hour=hour_start, minute=0, second=0, microsecond=0)
                else:
                    cursor = cursor.replace(hour=hour_start, minute=0, second=0, microsecond=0)
                continue
            end = cursor + timedelta(minutes=duration_minutes)
            slots.append((cursor, end))
            cursor += timedelta(hours=2)
        return slots

    def attach_slots(
        self,
        db: Session,
        session: InterviewSession,
        proposed_by: UUID,
        slot_times: list[tuple[datetime, datetime]],
    ) -> list[InterviewSlotSuggestion]:
        created: list[InterviewSlotSuggestion] = []
        for starts_at, ends_at in slot_times:
            row = InterviewSlotSuggestion(
                session_id=session.id,
                starts_at=starts_at,
                ends_at=ends_at,
                proposed_by=proposed_by,
                is_selected=False,
            )
            db.add(row)
            created.append(row)
        session.confirmation_status = ScheduleConfirmationStatus.PENDING
        db.add(session)
        db.commit()
        for row in created:
            db.refresh(row)
        return created

    def notify_candidate_of_slots(self, db: Session, session: InterviewSession) -> None:
        job = db.get(JobSpecification, session.job_spec_id)
        role = job.title if job else "the role"
        link = f"{settings.frontend_base_url}/candidate/sessions"
        self.notifications.notify(
            db,
            user_id=session.candidate_user_id,
            title=f"Interview slots available for {role}",
            body=(
                f"Your recruiter suggested interview slots for {role}. "
                "Please confirm a slot or request a reschedule in your candidate portal."
            ),
            link=link,
            related_session_id=session.id,
            send_email=True,
        )

    def confirm_slot(
        self,
        db: Session,
        session: InterviewSession,
        slot_id: UUID,
        candidate_note: str | None = None,
    ) -> InterviewSession:
        slot = (
            db.query(InterviewSlotSuggestion)
            .filter(InterviewSlotSuggestion.id == slot_id, InterviewSlotSuggestion.session_id == session.id)
            .first()
        )
        if slot is None:
            raise ValueError("Slot not found for this session")

        for existing in db.query(InterviewSlotSuggestion).filter(InterviewSlotSuggestion.session_id == session.id):
            existing.is_selected = existing.id == slot.id
            db.add(existing)

        session.scheduled_at = slot.starts_at
        session.confirmation_status = ScheduleConfirmationStatus.CONFIRMED
        session.confirmed_at = datetime.now(timezone.utc)
        session.candidate_note = candidate_note
        db.add(session)

        application = (
            db.query(JobApplication)
            .filter(
                JobApplication.job_spec_id == session.job_spec_id,
                JobApplication.candidate_user_id == session.candidate_user_id,
            )
            .first()
        )
        if application:
            application.stage = PipelineStage.INTERVIEW
            db.add(application)

        db.commit()
        db.refresh(session)

        job = db.get(JobSpecification, session.job_spec_id)
        role = job.title if job else "the role"
        note = candidate_note or "No note provided."
        self.notifications.notify(
            db,
            user_id=session.recruiter_id,
            title=f"Candidate confirmed interview for {role}",
            body=(
                f"The candidate confirmed the slot starting at {slot.starts_at.isoformat()}. "
                f"Note: {note}"
            ),
            link=f"{settings.frontend_base_url}/recruiter/scheduling",
            related_session_id=session.id,
            send_email=True,
        )
        return session

    def request_reschedule(
        self,
        db: Session,
        session: InterviewSession,
        candidate_note: str | None = None,
    ) -> InterviewSession:
        session.confirmation_status = ScheduleConfirmationStatus.RESCHEDULE_REQUESTED
        session.candidate_note = candidate_note
        session.confirmed_at = None
        for slot in db.query(InterviewSlotSuggestion).filter(InterviewSlotSuggestion.session_id == session.id):
            slot.is_selected = False
            db.add(slot)
        db.add(session)
        db.commit()
        db.refresh(session)

        job = db.get(JobSpecification, session.job_spec_id)
        role = job.title if job else "the role"
        note = candidate_note or "No note provided."
        self.notifications.notify(
            db,
            user_id=session.recruiter_id,
            title=f"Reschedule requested for {role}",
            body=f"The candidate requested a new interview slot. Note: {note}",
            link=f"{settings.frontend_base_url}/recruiter/scheduling",
            related_session_id=session.id,
            send_email=True,
        )
        return session

    def send_candidate_message(
        self,
        db: Session,
        session: InterviewSession,
        candidate_note: str,
    ) -> InterviewSession:
        note = candidate_note.strip()
        if not note:
            raise ValueError("Message cannot be empty")
        session.candidate_note = note
        db.add(session)
        db.commit()
        db.refresh(session)

        job = db.get(JobSpecification, session.job_spec_id)
        role = job.title if job else "the role"
        self.notifications.notify(
            db,
            user_id=session.recruiter_id,
            title=f"Message from candidate about {role}",
            body=note,
            link=f"{settings.frontend_base_url}/recruiter/scheduling",
            related_session_id=session.id,
            send_email=True,
        )
        return session

    def ensure_application_for_session(self, db: Session, session: InterviewSession, match_score: float | None) -> JobApplication:
        existing = (
            db.query(JobApplication)
            .filter(
                JobApplication.job_spec_id == session.job_spec_id,
                JobApplication.candidate_user_id == session.candidate_user_id,
            )
            .first()
        )
        if existing:
            existing.stage = PipelineStage.SHORTLISTED
            existing.gap_analysis_id = session.gap_analysis_id
            existing.cv_id = session.cv_id
            existing.match_score = match_score
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

        application = JobApplication(
            job_spec_id=session.job_spec_id,
            candidate_user_id=session.candidate_user_id,
            cv_id=session.cv_id,
            gap_analysis_id=session.gap_analysis_id,
            recruiter_id=session.recruiter_id,
            stage=PipelineStage.SHORTLISTED,
            match_score=match_score,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application
