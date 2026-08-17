"""Bridge hiring stages to interview sessions so Scheduling stays in sync."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    CandidateCv,
    GapAnalysis,
    InterviewQuestion,
    InterviewSession,
    InterviewSessionStatus,
    JobApplication,
    JobSpecification,
    QuestionPlan,
    QuestionSource,
    User,
)
from app.services.gap_analysis import GapAnalysisService
from app.services.question_generation import QuestionGenerationService


class HiringBridgeService:
    def __init__(self) -> None:
        self.gap_service = GapAnalysisService()
        self.question_service = QuestionGenerationService()

    def ensure_session_for_application(
        self,
        db: Session,
        application: JobApplication,
        recruiter_id: UUID,
    ) -> InterviewSession | None:
        """Create (or reuse) an interview session when a candidate is shortlisted."""
        if application.cv_id is None:
            return None

        existing = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.job_spec_id == application.job_spec_id,
                InterviewSession.candidate_user_id == application.candidate_user_id,
                InterviewSession.recruiter_id == recruiter_id,
                InterviewSession.status.in_(
                    [InterviewSessionStatus.SCHEDULED, InterviewSessionStatus.IN_PROGRESS]
                ),
            )
            .order_by(InterviewSession.created_at.desc())
            .first()
        )
        if existing:
            return existing

        job = db.get(JobSpecification, application.job_spec_id)
        cv = db.get(CandidateCv, application.cv_id)
        candidate = db.get(User, application.candidate_user_id)
        if job is None or cv is None or candidate is None:
            return None

        analysis = None
        if application.gap_analysis_id:
            analysis = db.get(GapAnalysis, application.gap_analysis_id)
        if analysis is None:
            analysis = (
                db.query(GapAnalysis)
                .filter(GapAnalysis.cv_id == cv.id, GapAnalysis.job_spec_id == job.id)
                .order_by(GapAnalysis.created_at.desc())
                .first()
            )
        if analysis is None:
            analysis = self.gap_service.analyse(db, cv, job, recruiter_id)

        application.gap_analysis_id = analysis.id
        application.match_score = analysis.match_score
        db.add(application)
        db.flush()

        plan = (
            db.query(QuestionPlan)
            .filter(
                QuestionPlan.gap_analysis_id == analysis.id,
                QuestionPlan.created_by == recruiter_id,
            )
            .order_by(QuestionPlan.created_at.desc())
            .first()
        )
        questions: list[InterviewQuestion] = []
        if plan is None:
            plan, questions = self.question_service.generate_plan(db, analysis, cv, job, recruiter_id)
        else:
            questions = (
                db.query(InterviewQuestion)
                .filter(InterviewQuestion.plan_id == plan.id, InterviewQuestion.approved.is_(True))
                .order_by(InterviewQuestion.sort_order.asc())
                .all()
            )
            if not questions:
                fallback = InterviewQuestion(
                    plan_id=plan.id,
                    text=f"Tell us about your experience relevant to the {job.title} role.",
                    topic="background",
                    question_type="behavioral",
                    source=QuestionSource.RECRUITER,
                    approved=True,
                    sort_order=0,
                )
                db.add(fallback)
                db.flush()
                questions = [fallback]

        session = InterviewSession(
            question_plan_id=plan.id,
            gap_analysis_id=analysis.id,
            cv_id=cv.id,
            job_spec_id=job.id,
            recruiter_id=recruiter_id,
            candidate_user_id=candidate.id,
            status=InterviewSessionStatus.SCHEDULED,
            follow_up_limit=1,
            current_question_index=0,
            current_follow_up_count=0,
            current_plan_question_id=questions[0].id if questions else None,
            scheduled_at=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
