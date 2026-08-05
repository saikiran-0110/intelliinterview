"""Generate candidate-facing interview feedback summaries."""

from __future__ import annotations

import json
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CandidateFeedback, InterviewReport, InterviewSession, JobSpecification


def _baseline_feedback(report: InterviewReport, job_title: str) -> dict:
    strong = list(report.strengths or [])[:5]
    improve = list(report.weaknesses or [])[:5]
    if not strong:
        strong = ["You completed the interview and provided answers for evaluation."]
    if not improve:
        improve = ["Add more concrete project examples and measurable outcomes in future answers."]
    tips = [
        f"Revisit the core requirements for {job_title} and prepare STAR-style examples.",
        "Practice explaining trade-offs and metrics for your technical decisions.",
        "Keep answers structured: context, actions, and results.",
    ]
    summary = (
        f"Thanks for completing the {job_title} interview. "
        f"Your stronger areas included: {', '.join(strong[:2])}. "
        f"To improve next time, focus on: {', '.join(improve[:2])}."
    )
    return {
        "summary": summary,
        "strong_answers": strong,
        "improvement_areas": improve,
        "focus_tips": tips,
        "model_version": "baseline",
    }


def _openai_feedback(report: InterviewReport, job_title: str, baseline: dict) -> dict | None:
    if not settings.openai_api_key:
        return None
    prompt = {
        "job_title": job_title,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "scores": {
            "technical_fit": report.technical_fit_score,
            "communication": report.communication_score,
            "problem_solving": report.problem_solving_score,
            "role_alignment": report.role_alignment_score,
        },
        "baseline": baseline,
        "instructions": (
            "Write candidate-facing feedback. Do NOT include hiring recommendations. "
            "Return JSON with keys: summary (string), strong_answers (string array), "
            "improvement_areas (string array), focus_tips (string array)."
        ),
    }
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You write constructive interview feedback for software engineering candidates.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        return {
            "summary": str(payload.get("summary") or baseline["summary"]),
            "strong_answers": payload.get("strong_answers") or baseline["strong_answers"],
            "improvement_areas": payload.get("improvement_areas") or baseline["improvement_areas"],
            "focus_tips": payload.get("focus_tips") or baseline["focus_tips"],
            "model_version": settings.openai_model,
        }
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, IndexError, TypeError):
        return None


class CandidateFeedbackService:
    def generate_for_report(self, db: Session, report: InterviewReport) -> CandidateFeedback:
        existing = (
            db.query(CandidateFeedback)
            .filter(CandidateFeedback.session_id == report.session_id)
            .first()
        )
        job = db.get(JobSpecification, report.job_spec_id)
        job_title = job.title if job else "the role"
        baseline = _baseline_feedback(report, job_title)
        polished = _openai_feedback(report, job_title, baseline) or baseline

        if existing:
            feedback = existing
        else:
            feedback = CandidateFeedback(
                session_id=report.session_id,
                candidate_user_id=report.candidate_user_id,
                report_id=report.id,
            )
            db.add(feedback)

        feedback.report_id = report.id
        feedback.summary = polished["summary"]
        feedback.strong_answers = polished["strong_answers"]
        feedback.improvement_areas = polished["improvement_areas"]
        feedback.focus_tips = polished["focus_tips"]
        feedback.model_version = polished["model_version"]
        db.commit()
        db.refresh(feedback)
        return feedback

    def list_for_candidate(self, db: Session, candidate_user_id: UUID) -> list[CandidateFeedback]:
        return (
            db.query(CandidateFeedback)
            .filter(CandidateFeedback.candidate_user_id == candidate_user_id)
            .order_by(CandidateFeedback.created_at.desc())
            .all()
        )

    def get_for_session(self, db: Session, session_id: UUID, candidate_user_id: UUID) -> CandidateFeedback | None:
        return (
            db.query(CandidateFeedback)
            .filter(
                CandidateFeedback.session_id == session_id,
                CandidateFeedback.candidate_user_id == candidate_user_id,
            )
            .first()
        )
