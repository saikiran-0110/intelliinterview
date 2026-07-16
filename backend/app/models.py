import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
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


class TurnRole(str, enum.Enum):
    INTERVIEWER = "INTERVIEWER"
    CANDIDATE = "CANDIDATE"


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


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
