"""Aggregate turn evaluations into a structured post-interview report."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    GapAnalysis,
    HiringRecommendation,
    InterviewQuestion,
    InterviewReport,
    InterviewSession,
    InterviewTurn,
    InterviewTurnEvaluation,
    JobSpecification,
    TurnRole,
    User,
)


PROBLEM_SOLVING_TYPES = {"problem_solving", "scenario", "system_design", "scenario_question"}
ROLE_ALIGNMENT_TYPES = {"role_alignment", "experience", "qualifications", "general"}


def _mean(values: list[float], default: float = 5.0) -> float:
    if not values:
        return default
    return round(sum(values) / len(values), 1)


def _unique_keep_order(items: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = item.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _recommendation_from_score(overall: float) -> HiringRecommendation:
    if overall >= 8.0:
        return HiringRecommendation.STRONG_HIRE
    if overall >= 6.5:
        return HiringRecommendation.HIRE
    if overall >= 5.0:
        return HiringRecommendation.HOLD
    return HiringRecommendation.NO_HIRE


def _recommendation_label(value: HiringRecommendation) -> str:
    return value.value.replace("_", " ").title()


def _build_summary(
    candidate_name: str,
    job_title: str,
    overall: float,
    recommendation: HiringRecommendation,
    strengths: list[str],
    weaknesses: list[str],
) -> str:
    strength_text = ", ".join(strengths[:3]) if strengths else "limited evidenced strengths"
    weakness_text = ", ".join(weaknesses[:3]) if weaknesses else "no major weaknesses flagged"
    return (
        f"{candidate_name} scored {overall}/10 overall for the {job_title} interview. "
        f"Recommendation: {_recommendation_label(recommendation)}. "
        f"Strengths include {strength_text}. Areas to watch include {weakness_text}."
    )


def _openai_polish_summary(
    candidate_name: str,
    job_title: str,
    scores: dict[str, float],
    evidence_items: list[dict[str, Any]],
    strengths: list[str],
    weaknesses: list[str],
    baseline_summary: str,
) -> str | None:
    if not settings.openai_api_key:
        return None

    prompt = {
        "candidate_name": candidate_name,
        "job_title": job_title,
        "scores": scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "evidence_items": evidence_items[:8],
        "baseline_summary": baseline_summary,
        "instructions": (
            "Write a concise recruiter recommendation summary (3-5 sentences). "
            "Ground every claim in the provided scores and evidence. "
            "Return JSON with key recommendation_summary."
        ),
    }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You write concise, evidence-based interview evaluation summaries for recruiters.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        summary = payload.get("recommendation_summary")
        return str(summary).strip() if summary else None
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, IndexError, TypeError):
        return None


class ReportGenerationService:
    def generate_for_session(self, db: Session, session: InterviewSession) -> InterviewReport:
        existing = (
            db.query(InterviewReport)
            .filter(InterviewReport.session_id == session.id)
            .first()
        )

        evaluations = (
            db.query(InterviewTurnEvaluation)
            .filter(InterviewTurnEvaluation.session_id == session.id)
            .all()
        )
        turns = {
            turn.id: turn
            for turn in db.query(InterviewTurn)
            .filter(InterviewTurn.session_id == session.id, InterviewTurn.role == TurnRole.CANDIDATE)
            .all()
        }
        questions = {
            question.id: question
            for question in db.query(InterviewQuestion)
            .filter(InterviewQuestion.plan_id == session.question_plan_id)
            .all()
        }

        technical_scores = [e.technical_score for e in evaluations if e.technical_score is not None]
        communication_scores = [
            e.communication_score for e in evaluations if e.communication_score is not None
        ]

        problem_scores: list[float] = []
        alignment_scores: list[float] = []
        strengths: list[str] = []
        weaknesses: list[str] = []
        evidence_items: list[dict[str, Any]] = []

        for evaluation in evaluations:
            turn = turns.get(evaluation.turn_id)
            question = questions.get(evaluation.plan_question_id) if evaluation.plan_question_id else None
            q_type = (question.question_type if question else "") or ""
            topic = (question.topic if question else "") or ""

            if evaluation.technical_score is not None:
                if q_type in PROBLEM_SOLVING_TYPES or "problem" in topic.lower() or "design" in topic.lower():
                    problem_scores.append(evaluation.technical_score)
                if q_type in ROLE_ALIGNMENT_TYPES or "experience" in topic.lower() or "role" in topic.lower():
                    alignment_scores.append(evaluation.technical_score)

            strengths.extend(str(item) for item in (evaluation.strengths or []))
            weaknesses.extend(str(item) for item in (evaluation.weaknesses or []))

            evidence_items.append(
                {
                    "turn_id": str(evaluation.turn_id),
                    "question_text": question.text if question else None,
                    "topic": question.topic if question else None,
                    "answer_excerpt": turn.content[:280] if turn else None,
                    "observations": evaluation.observations or [],
                    "evidence_quotes": evaluation.evidence_quotes or [],
                    "technical_score": evaluation.technical_score,
                    "communication_score": evaluation.communication_score,
                }
            )

        gap = db.get(GapAnalysis, session.gap_analysis_id)
        match_score = gap.match_score if gap and gap.match_score is not None else None
        alignment_from_gap = round((match_score / 10.0), 1) if match_score is not None else None

        technical_fit = _mean(technical_scores)
        communication = _mean(communication_scores)
        problem_solving = _mean(problem_scores, default=technical_fit)
        if alignment_scores and alignment_from_gap is not None:
            role_alignment = round(((_mean(alignment_scores) + alignment_from_gap) / 2), 1)
        elif alignment_scores:
            role_alignment = _mean(alignment_scores)
        elif alignment_from_gap is not None:
            role_alignment = alignment_from_gap
        else:
            role_alignment = technical_fit

        overall = round(
            technical_fit * 0.35
            + communication * 0.25
            + problem_solving * 0.20
            + role_alignment * 0.20,
            1,
        )
        recommendation = _recommendation_from_score(overall)
        cleaned_strengths = _unique_keep_order(strengths)
        cleaned_weaknesses = _unique_keep_order(weaknesses)

        candidate = db.get(User, session.candidate_user_id)
        job_spec = db.get(JobSpecification, session.job_spec_id)
        candidate_name = candidate.full_name if candidate else "Candidate"
        job_title = job_spec.title if job_spec else "the role"

        baseline_summary = _build_summary(
            candidate_name,
            job_title,
            overall,
            recommendation,
            cleaned_strengths,
            cleaned_weaknesses,
        )
        polished = _openai_polish_summary(
            candidate_name,
            job_title,
            {
                "technical_fit": technical_fit,
                "communication": communication,
                "problem_solving": problem_solving,
                "role_alignment": role_alignment,
                "overall": overall,
            },
            evidence_items,
            cleaned_strengths,
            cleaned_weaknesses,
            baseline_summary,
        )

        dimension_notes = {
            "technical_fit": f"Average technical score across {len(technical_scores)} evaluated answers.",
            "communication": f"Average communication score across {len(communication_scores)} evaluated answers.",
            "problem_solving": "Derived from scenario/problem-solving questions when available.",
            "role_alignment": "Combines role-focused answers with CV-to-job match signals when available.",
        }

        if existing:
            report = existing
        else:
            report = InterviewReport(
                session_id=session.id,
                recruiter_id=session.recruiter_id,
                candidate_user_id=session.candidate_user_id,
                cv_id=session.cv_id,
                job_spec_id=session.job_spec_id,
            )
            db.add(report)

        report.technical_fit_score = technical_fit
        report.communication_score = communication
        report.problem_solving_score = problem_solving
        report.role_alignment_score = role_alignment
        report.overall_score = overall
        report.recommendation = recommendation
        report.recommendation_summary = polished or baseline_summary
        report.strengths = cleaned_strengths
        report.weaknesses = cleaned_weaknesses
        report.evidence_items = evidence_items
        report.dimension_notes = dimension_notes
        report.model_version = settings.openai_model if settings.openai_api_key else "baseline"

        db.commit()
        db.refresh(report)
        return report

    def get_for_session(self, db: Session, session_id: UUID) -> InterviewReport | None:
        return db.query(InterviewReport).filter(InterviewReport.session_id == session_id).first()
