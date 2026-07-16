from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    GapAnalysis,
    InterviewQuestion,
    InterviewSession,
    InterviewSessionStatus,
    InterviewTurn,
    InterviewTurnEvaluation,
    JobSpecification,
    QuestionPlan,
    TurnRole,
    User,
    UserRole,
)
from app.session_schemas import (
    InterviewSessionResponse,
    InterviewTurnResponse,
    SessionCreateRequest,
    SessionQuestionProgress,
    SessionSummaryResponse,
    SubmitAnswerRequest,
    TurnEvaluationResponse,
)
from app.services.interview_agent import InterviewAgentService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
agent = InterviewAgentService()


def _approved_questions(db: Session, plan_id: UUID) -> list[InterviewQuestion]:
    return (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.plan_id == plan_id, InterviewQuestion.approved.is_(True))
        .order_by(InterviewQuestion.sort_order.asc())
        .all()
    )


def _next_sequence(db: Session, session_id: UUID) -> int:
    count = db.query(InterviewTurn).filter(InterviewTurn.session_id == session_id).count()
    return count + 1


def _evaluation_response(evaluation: InterviewTurnEvaluation | None) -> TurnEvaluationResponse | None:
    if evaluation is None:
        return None
    return TurnEvaluationResponse(
        technical_score=evaluation.technical_score,
        communication_score=evaluation.communication_score,
        observations=evaluation.observations or [],
        evidence_quotes=evaluation.evidence_quotes or [],
        strengths=evaluation.strengths or [],
        weaknesses=evaluation.weaknesses or [],
        should_follow_up=evaluation.should_follow_up,
        follow_up_question=evaluation.follow_up_question,
        advance_question=evaluation.advance_question,
        model_version=evaluation.model_version,
    )


def _session_response(db: Session, session: InterviewSession) -> InterviewSessionResponse:
    candidate = db.get(User, session.candidate_user_id)
    job_spec = db.get(JobSpecification, session.job_spec_id)
    plan = db.get(QuestionPlan, session.question_plan_id)
    questions = _approved_questions(db, session.question_plan_id)
    total = len(questions)
    current_q = None
    if session.current_plan_question_id:
        current_q = db.get(InterviewQuestion, session.current_plan_question_id)
    elif 0 <= session.current_question_index < total:
        current_q = questions[session.current_question_index]

    turns = (
        db.query(InterviewTurn)
        .filter(InterviewTurn.session_id == session.id)
        .order_by(InterviewTurn.sequence.asc())
        .all()
    )
    evaluations = {
        item.turn_id: item
        for item in db.query(InterviewTurnEvaluation)
        .filter(InterviewTurnEvaluation.session_id == session.id)
        .all()
    }

    turn_responses = [
        InterviewTurnResponse(
            id=turn.id,
            sequence=turn.sequence,
            role=turn.role,
            content=turn.content,
            plan_question_id=turn.plan_question_id,
            is_follow_up=turn.is_follow_up,
            follow_up_index=turn.follow_up_index,
            created_at=turn.created_at,
            evaluation=_evaluation_response(evaluations.get(turn.id)),
        )
        for turn in turns
    ]

    return InterviewSessionResponse(
        id=session.id,
        question_plan_id=session.question_plan_id,
        gap_analysis_id=session.gap_analysis_id,
        cv_id=session.cv_id,
        job_spec_id=session.job_spec_id,
        recruiter_id=session.recruiter_id,
        candidate_user_id=session.candidate_user_id,
        candidate_name=candidate.full_name if candidate else "Unknown",
        candidate_email=candidate.email if candidate else "",
        job_title=job_spec.title if job_spec else "Unknown role",
        plan_title=plan.title if plan else "Interview plan",
        status=session.status,
        follow_up_limit=session.follow_up_limit,
        current_question_index=session.current_question_index,
        current_follow_up_count=session.current_follow_up_count,
        current_plan_question_id=session.current_plan_question_id,
        progress=SessionQuestionProgress(
            index=min(session.current_question_index + 1, max(total, 1)),
            total=total,
            question_id=current_q.id if current_q else None,
            question_text=current_q.text if current_q else None,
            topic=current_q.topic if current_q else None,
        ),
        turns=turn_responses,
        scheduled_at=session.scheduled_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
    )


def _summary(db: Session, session: InterviewSession) -> SessionSummaryResponse:
    candidate = db.get(User, session.candidate_user_id)
    job_spec = db.get(JobSpecification, session.job_spec_id)
    plan = db.get(QuestionPlan, session.question_plan_id)
    total = len(_approved_questions(db, session.question_plan_id))
    return SessionSummaryResponse(
        id=session.id,
        status=session.status,
        candidate_name=candidate.full_name if candidate else "Unknown",
        candidate_email=candidate.email if candidate else "",
        job_title=job_spec.title if job_spec else "Unknown role",
        plan_title=plan.title if plan else "Interview plan",
        current_question_index=session.current_question_index,
        total_questions=total,
        created_at=session.created_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


def _get_accessible_session(db: Session, session_id: UUID, user: User) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user.role == UserRole.RECRUITER and session.recruiter_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user.role == UserRole.CANDIDATE and session.candidate_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> InterviewSessionResponse:
    plan = db.get(QuestionPlan, request.question_plan_id)
    if plan is None or plan.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question plan not found")

    questions = _approved_questions(db, plan.id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question plan has no approved questions",
        )

    analysis = db.get(GapAnalysis, plan.gap_analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked gap analysis not found")

    candidate = (
        db.query(User)
        .filter(User.email == request.candidate_email.lower(), User.role == UserRole.CANDIDATE)
        .first()
    )
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate account not found. Ask the candidate to register first.",
        )

    session = InterviewSession(
        question_plan_id=plan.id,
        gap_analysis_id=analysis.id,
        cv_id=analysis.cv_id,
        job_spec_id=analysis.job_spec_id,
        recruiter_id=current_user.id,
        candidate_user_id=candidate.id,
        status=InterviewSessionStatus.SCHEDULED,
        follow_up_limit=request.follow_up_limit,
        current_question_index=0,
        current_follow_up_count=0,
        current_plan_question_id=questions[0].id,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(db, session)


@router.get("", response_model=list[SessionSummaryResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SessionSummaryResponse]:
    query = db.query(InterviewSession)
    if current_user.role == UserRole.RECRUITER:
        query = query.filter(InterviewSession.recruiter_id == current_user.id)
    elif current_user.role == UserRole.CANDIDATE:
        query = query.filter(InterviewSession.candidate_user_id == current_user.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    sessions = query.order_by(InterviewSession.created_at.desc()).all()
    return [_summary(db, item) for item in sessions]


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewSessionResponse:
    session = _get_accessible_session(db, session_id, current_user)
    return _session_response(db, session)


@router.post("/{session_id}/start", response_model=InterviewSessionResponse)
def start_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> InterviewSessionResponse:
    session = _get_accessible_session(db, session_id, current_user)
    if session.status == InterviewSessionStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session already completed")
    if session.status == InterviewSessionStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session was cancelled")

    questions = _approved_questions(db, session.question_plan_id)
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No approved questions available")

    if session.status == InterviewSessionStatus.SCHEDULED:
        first_question = questions[0]
        session.status = InterviewSessionStatus.IN_PROGRESS
        session.started_at = datetime.now(timezone.utc)
        session.current_question_index = 0
        session.current_follow_up_count = 0
        session.current_plan_question_id = first_question.id

        existing_turns = db.query(InterviewTurn).filter(InterviewTurn.session_id == session.id).count()
        if existing_turns == 0:
            turn = InterviewTurn(
                session_id=session.id,
                sequence=_next_sequence(db, session.id),
                role=TurnRole.INTERVIEWER,
                content=first_question.text,
                plan_question_id=first_question.id,
                is_follow_up=False,
                follow_up_index=0,
            )
            db.add(turn)

        db.add(session)
        db.commit()
        db.refresh(session)

    return _session_response(db, session)


@router.post("/{session_id}/answer", response_model=InterviewSessionResponse)
def submit_answer(
    session_id: UUID,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
) -> InterviewSessionResponse:
    session = _get_accessible_session(db, session_id, current_user)
    if session.status != InterviewSessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not in progress")

    questions = _approved_questions(db, session.question_plan_id)
    if not questions or session.current_question_index >= len(questions):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active question in this session")

    current_question = questions[session.current_question_index]
    answer_text = request.answer.strip()
    if not answer_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Answer cannot be empty")

    candidate_turn = InterviewTurn(
        session_id=session.id,
        sequence=_next_sequence(db, session.id),
        role=TurnRole.CANDIDATE,
        content=answer_text,
        plan_question_id=current_question.id,
        is_follow_up=session.current_follow_up_count > 0,
        follow_up_index=session.current_follow_up_count,
    )
    db.add(candidate_turn)
    db.flush()

    recent_turns = (
        db.query(InterviewTurn)
        .filter(InterviewTurn.session_id == session.id)
        .order_by(InterviewTurn.sequence.asc())
        .all()
    )
    job_spec = db.get(JobSpecification, session.job_spec_id)
    job_title = job_spec.title if job_spec else "Software Engineer"

    evaluation_data = agent.evaluate_answer(
        answer=answer_text,
        question=current_question,
        recent_turns=recent_turns,
        follow_up_count=session.current_follow_up_count,
        follow_up_limit=session.follow_up_limit,
        job_title=job_title,
    )

    evaluation = InterviewTurnEvaluation(
        session_id=session.id,
        turn_id=candidate_turn.id,
        plan_question_id=current_question.id,
        technical_score=evaluation_data["technical_score"],
        communication_score=evaluation_data["communication_score"],
        observations=evaluation_data["observations"],
        evidence_quotes=evaluation_data["evidence_quotes"],
        strengths=evaluation_data["strengths"],
        weaknesses=evaluation_data["weaknesses"],
        should_follow_up=evaluation_data["should_follow_up"],
        follow_up_question=evaluation_data.get("follow_up_question"),
        advance_question=evaluation_data["advance_question"],
        model_version=evaluation_data.get("model_version"),
        raw_model_response=evaluation_data.get("raw_model_response"),
    )
    db.add(evaluation)

    if evaluation_data["should_follow_up"] and evaluation_data.get("follow_up_question"):
        session.current_follow_up_count += 1
        follow_up_turn = InterviewTurn(
            session_id=session.id,
            sequence=_next_sequence(db, session.id),
            role=TurnRole.INTERVIEWER,
            content=evaluation_data["follow_up_question"],
            plan_question_id=current_question.id,
            is_follow_up=True,
            follow_up_index=session.current_follow_up_count,
        )
        db.add(follow_up_turn)
    else:
        next_index = session.current_question_index + 1
        if next_index >= len(questions):
            session.status = InterviewSessionStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
            session.current_question_index = next_index
            session.current_plan_question_id = None
            closing = InterviewTurn(
                session_id=session.id,
                sequence=_next_sequence(db, session.id),
                role=TurnRole.INTERVIEWER,
                content=(
                    "Thank you. That concludes the interview questions. "
                    "Your responses have been recorded for the recruiter report."
                ),
                plan_question_id=None,
                is_follow_up=False,
                follow_up_index=0,
            )
            db.add(closing)
        else:
            next_question = questions[next_index]
            session.current_question_index = next_index
            session.current_follow_up_count = 0
            session.current_plan_question_id = next_question.id
            next_turn = InterviewTurn(
                session_id=session.id,
                sequence=_next_sequence(db, session.id),
                role=TurnRole.INTERVIEWER,
                content=next_question.text,
                plan_question_id=next_question.id,
                is_follow_up=False,
                follow_up_index=0,
            )
            db.add(next_turn)

    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_response(db, session)
