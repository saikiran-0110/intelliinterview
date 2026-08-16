import enum
import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    RECRUITER = "RECRUITER"
    CANDIDATE = "CANDIDATE"


class InterviewSessionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class QuestionSource(str, enum.Enum):
    AI = "AI"
    RECRUITER = "RECRUITER"


class HiringRecommendation(str, enum.Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    HOLD = "HOLD"
    NO_HIRE = "NO_HIRE"


class TurnRole(str, enum.Enum):
    INTERVIEWER = "INTERVIEWER"
    CANDIDATE = "CANDIDATE"


class ScheduleConfirmationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    RESCHEDULE_REQUESTED = "RESCHEDULE_REQUESTED"
    DECLINED = "DECLINED"


class PipelineStage(str, enum.Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class BiasAlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"


class WorkMode(str, enum.Enum):
    ONSITE = "ONSITE"
    HYBRID = "HYBRID"
    REMOTE = "REMOTE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JobSpecification(Base):
    __tablename__ = "job_specifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    parsed_requirements: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    department: Mapped[Optional[str]] = mapped_column(String(120))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employment_type", native_enum=False),
        nullable=False,
        default=EmploymentType.FULL_TIME,
    )
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode, name="work_mode", native_enum=False),
        nullable=False,
        default=WorkMode.HYBRID,
    )
    salary_min_gbp: Mapped[Optional[float]] = mapped_column(Float)
    salary_max_gbp: Mapped[Optional[float]] = mapped_column(Float)
    years_experience_min: Mapped[Optional[int]] = mapped_column(Integer)
    closing_date: Mapped[Optional[date]] = mapped_column(Date)
    benefits: Mapped[Optional[str]] = mapped_column(Text)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CandidateCv(Base):
    __tablename__ = "candidate_cvs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_name: Mapped[str] = mapped_column(String(120), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    parsed_profile: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    content_type: Mapped[Optional[str]] = mapped_column(String(120))
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GapAnalysis(Base):
    __tablename__ = "gap_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_cvs.id"), nullable=False)
    job_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_specifications.id"), nullable=False
    )
    strong_matches: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    partial_matches: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    gaps: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    experience_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    qualifications_analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    evidence_passages: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    narrative_summary: Mapped[str] = mapped_column(Text, nullable=False)
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuestionPlan(Base):
    __tablename__ = "question_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gap_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gap_analyses.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_plans.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    question_type: Mapped[str] = mapped_column(String(60), nullable=False, default="technical")
    source: Mapped[QuestionSource] = mapped_column(
        Enum(QuestionSource, name="question_source", native_enum=False), nullable=False
    )
    skill_ref: Mapped[Optional[str]] = mapped_column(String(120))
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_plans.id"), nullable=False, index=True
    )
    gap_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gap_analyses.id"), nullable=False
    )
    cv_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_cvs.id"), nullable=False)
    job_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_specifications.id"), nullable=False
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[InterviewSessionStatus] = mapped_column(
        Enum(InterviewSessionStatus, name="interview_session_status", native_enum=False),
        nullable=False,
        default=InterviewSessionStatus.SCHEDULED,
    )
    follow_up_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_follow_up_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_plan_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id")
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confirmation_status: Mapped[ScheduleConfirmationStatus] = mapped_column(
        Enum(ScheduleConfirmationStatus, name="schedule_confirmation_status", native_enum=False),
        nullable=False,
        default=ScheduleConfirmationStatus.PENDING,
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    candidate_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class InterviewSlotSuggestion(Base):
    __tablename__ = "interview_slot_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    proposed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", native_enum=False),
        nullable=False,
        default=NotificationChannel.IN_APP,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String(255))
    related_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id")
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_specifications.id"), nullable=False, index=True
    )
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cv_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_cvs.id"))
    gap_analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("gap_analyses.id"))
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, name="pipeline_stage", native_enum=False),
        nullable=False,
        default=PipelineStage.APPLIED,
    )
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    contact_full_name: Mapped[Optional[str]] = mapped_column(String(120))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(40))
    contact_linkedin: Mapped[Optional[str]] = mapped_column(String(255))
    current_location: Mapped[Optional[str]] = mapped_column(String(255))
    expected_salary_gbp: Mapped[Optional[float]] = mapped_column(Float)
    right_to_work_uk: Mapped[Optional[bool]] = mapped_column(Boolean)
    cover_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CandidateFeedback(Base):
    __tablename__ = "candidate_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True
    )
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_reports.id"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strong_answers: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    focus_tips: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    model_version: Mapped[Optional[str]] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BiasAlert(Base):
    __tablename__ = "bias_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[BiasAlertSeverity] = mapped_column(
        Enum(BiasAlertSeverity, name="bias_alert_severity", native_enum=False),
        nullable=False,
        default=BiasAlertSeverity.MEDIUM,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[TurnRole] = mapped_column(
        Enum(TurnRole, name="turn_role", native_enum=False), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    plan_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id")
    )
    is_follow_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    follow_up_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewTurnEvaluation(Base):
    __tablename__ = "interview_turn_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True
    )
    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_turns.id"), nullable=False, unique=True
    )
    plan_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_questions.id")
    )
    technical_score: Mapped[Optional[float]] = mapped_column(Float)
    communication_score: Mapped[Optional[float]] = mapped_column(Float)
    observations: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    evidence_quotes: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    should_follow_up: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    follow_up_question: Mapped[Optional[str]] = mapped_column(Text)
    advance_question: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(60))
    raw_model_response: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    cv_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_cvs.id"), nullable=False)
    job_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_specifications.id"), nullable=False
    )
    technical_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False)
    problem_solving_score: Mapped[float] = mapped_column(Float, nullable=False)
    role_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[HiringRecommendation] = mapped_column(
        Enum(HiringRecommendation, name="hiring_recommendation", native_enum=False),
        nullable=False,
    )
    recommendation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    evidence_items: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    dimension_notes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    model_version: Mapped[Optional[str]] = mapped_column(String(60))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PreparationPack(Base):
    __tablename__ = "preparation_packs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cv_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_cvs.id"), nullable=False)
    job_spec_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_specifications.id"), nullable=False
    )
    practice_questions: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    guidance: Mapped[str] = mapped_column(Text, nullable=False)
    focus_areas: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    model_version: Mapped[Optional[str]] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
