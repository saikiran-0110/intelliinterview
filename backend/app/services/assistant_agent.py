"""Recruiter AI assistant with tool-style queries over candidate data (no LangChain dependency)."""

from __future__ import annotations

import json
import logging
import re
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CandidateCv,
    GapAnalysis,
    InterviewQuestion,
    InterviewReport,
    InterviewSession,
    InterviewSessionStatus,
    JobApplication,
    JobSpecification,
    PipelineStage,
    QuestionPlan,
    ScheduleConfirmationStatus,
    User,
)
from app.services.llm_json import as_text

logger = logging.getLogger(__name__)


def _plural(count: int) -> str:
    return "" if count == 1 else "s"


class AssistantAgentService:
    def answer(self, db: Session, recruiter_id: UUID, message: str) -> dict:
        tools_used: list[str] = []
        structured: dict = {"matches": [], "summary": None, "applications": []}
        lower = message.lower()

        job = self._resolve_job(db, recruiter_id, message)
        if any(token in lower for token in ["best candidate", "top candidate", "rank", "shortlist", "match"]):
            tools_used.append("find_best_candidates")
            structured["matches"] = self._best_candidates(db, recruiter_id, job)
        if any(token in lower for token in ["summar", "cv overview", "resume"]):
            tools_used.append("summarise_cv")
            structured["summary"] = self._summarise_cv(db, recruiter_id, message)
        if any(token in lower for token in ["application", "pipeline", "stage"]):
            tools_used.append("list_applications")
            structured["applications"] = self._list_applications(db, recruiter_id, job)

        if not tools_used:
            tools_used.append("find_best_candidates")
            structured["matches"] = self._best_candidates(db, recruiter_id, job)

        answer = self._compose_answer(message, structured, job)
        polished = self._openai_polish(message, structured, answer)
        return {
            "answer": polished or answer,
            "structured": structured,
            "tools_used": tools_used,
        }

    def next_actions(self, db: Session, recruiter_id: UUID) -> list[dict]:
        """Deterministic pipeline-rules panel. No model call: these are rules over the
        recruiter's own data, matching the principle that deterministic logic owns
        anything a recruiter acts on."""
        items: list[dict] = []

        planned_gap_ids = {
            row[0]
            for row in db.query(QuestionPlan.gap_analysis_id)
            .filter(QuestionPlan.created_by == recruiter_id)
            .all()
        }
        shortlisted_by_job: dict[UUID, int] = {}
        for app in (
            db.query(JobApplication)
            .filter(
                JobApplication.recruiter_id == recruiter_id,
                JobApplication.stage == PipelineStage.SHORTLISTED,
                JobApplication.gap_analysis_id.isnot(None),
            )
            .all()
        ):
            if app.gap_analysis_id in planned_gap_ids:
                continue
            shortlisted_by_job[app.job_spec_id] = shortlisted_by_job.get(app.job_spec_id, 0) + 1
        for job_id, count in shortlisted_by_job.items():
            job_title = self._job_title(db, job_id)
            items.append(
                {
                    "id": f"shortlisted-no-plan:{job_id}",
                    "priority": 0,
                    "title": f"{count} shortlisted candidate{_plural(count)} with no question plan for {job_title}",
                    "detail": f"Build an interview question plan before scheduling for {job_title}.",
                    "cta_label": "Plan questions",
                    "cta_path": "/recruiter/questions",
                }
            )

        unconfirmed = (
            db.query(InterviewSession)
            .filter(
                InterviewSession.recruiter_id == recruiter_id,
                InterviewSession.status == InterviewSessionStatus.SCHEDULED,
                InterviewSession.confirmation_status != ScheduleConfirmationStatus.CONFIRMED,
            )
            .count()
        )
        if unconfirmed:
            items.append(
                {
                    "id": "sessions-unconfirmed",
                    "priority": 0,
                    "title": f"{unconfirmed} scheduled interview{_plural(unconfirmed)} awaiting confirmation",
                    "detail": "These candidates have not confirmed their interview slot yet.",
                    "cta_label": "Open scheduling",
                    "cta_path": "/recruiter/scheduling",
                }
            )

        pending_by_job: dict[UUID, int] = {}
        for app in (
            db.query(JobApplication)
            .join(JobSpecification, JobApplication.job_spec_id == JobSpecification.id)
            .filter(
                JobApplication.recruiter_id == recruiter_id,
                JobApplication.stage.in_([PipelineStage.APPLIED, PipelineStage.SCREENING]),
                JobSpecification.is_open.is_(True),
            )
            .all()
        ):
            pending_by_job[app.job_spec_id] = pending_by_job.get(app.job_spec_id, 0) + 1
        for job_id, count in pending_by_job.items():
            job_title = self._job_title(db, job_id)
            items.append(
                {
                    "id": f"rank-applicants:{job_id}",
                    "priority": 1,
                    "title": f"{count} applicant{_plural(count)} to rank for {job_title}",
                    "detail": f"New or screening-stage applicants are waiting to be ranked for {job_title}.",
                    "cta_label": "Rank applicants",
                    "cta_path": "/recruiter/ranking",
                }
            )

        scheduled_plan_ids = {
            row[0]
            for row in db.query(InterviewSession.question_plan_id)
            .filter(InterviewSession.recruiter_id == recruiter_id)
            .all()
        }
        ready_by_job: dict[UUID | None, int] = {}
        for plan in db.query(QuestionPlan).filter(QuestionPlan.created_by == recruiter_id).all():
            if plan.id in scheduled_plan_ids:
                continue
            has_approved = (
                db.query(InterviewQuestion)
                .filter(InterviewQuestion.plan_id == plan.id, InterviewQuestion.approved.is_(True))
                .first()
            )
            if not has_approved:
                continue
            analysis = db.get(GapAnalysis, plan.gap_analysis_id)
            job_id = analysis.job_spec_id if analysis else None
            ready_by_job[job_id] = ready_by_job.get(job_id, 0) + 1
        for job_id, count in ready_by_job.items():
            job_title = self._job_title(db, job_id) if job_id else "a role"
            items.append(
                {
                    "id": f"create-session:{job_id or 'unknown'}",
                    "priority": 1,
                    "title": f"{count} question plan{_plural(count)} ready for a session for {job_title}",
                    "detail": f"Approved questions exist but no interview session has been created for {job_title}.",
                    "cta_label": "Create session",
                    "cta_path": "/recruiter/sessions/new",
                }
            )

        completed_with_report = (
            db.query(InterviewSession)
            .join(InterviewReport, InterviewReport.session_id == InterviewSession.id)
            .filter(
                InterviewSession.recruiter_id == recruiter_id,
                InterviewSession.status == InterviewSessionStatus.COMPLETED,
            )
            .count()
        )
        if completed_with_report:
            items.append(
                {
                    "id": "reports-ready",
                    "priority": 2,
                    "title": (
                        f"{completed_with_report} completed interview report"
                        f"{_plural(completed_with_report)} ready to review"
                    ),
                    "detail": "Review scores and recommendations from completed interviews.",
                    "cta_label": "Open reports",
                    "cta_path": "/recruiter/reports",
                }
            )

        applied_job_ids = {
            row[0]
            for row in db.query(JobApplication.job_spec_id)
            .filter(JobApplication.recruiter_id == recruiter_id)
            .all()
        }
        open_jobs = (
            db.query(JobSpecification)
            .filter(JobSpecification.created_by == recruiter_id, JobSpecification.is_open.is_(True))
            .all()
        )
        empty_jobs = sum(1 for job in open_jobs if job.id not in applied_job_ids)
        if empty_jobs:
            items.append(
                {
                    "id": "open-roles-no-applications",
                    "priority": 3,
                    "title": f"{empty_jobs} open role{_plural(empty_jobs)} with no applications yet",
                    "detail": "Consider sharing these roles more widely.",
                    "cta_label": "Open hiring board",
                    "cta_path": "/recruiter/jobs",
                }
            )

        if not items:
            items.append(
                {
                    "id": "nothing-blocked",
                    "priority": 4,
                    "title": "Nothing is blocked right now",
                    "detail": "Your pipeline has no outstanding blockers.",
                    "cta_label": None,
                    "cta_path": None,
                }
            )

        items.sort(key=lambda item: item["priority"])
        return items[:6]

    def _job_title(self, db: Session, job_id: UUID) -> str:
        job = db.get(JobSpecification, job_id)
        return job.title if job else "a role"

    def _resolve_job(self, db: Session, recruiter_id: UUID, message: str) -> JobSpecification | None:
        jobs = (
            db.query(JobSpecification)
            .filter(JobSpecification.created_by == recruiter_id)
            .order_by(JobSpecification.created_at.desc())
            .all()
        )
        lower = message.lower()
        for job in jobs:
            if job.title.lower() in lower:
                return job
        return jobs[0] if jobs else None

    def _best_candidates(self, db: Session, recruiter_id: UUID, job: JobSpecification | None) -> list[dict]:
        query = db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter_id)
        if job:
            query = query.filter(JobApplication.job_spec_id == job.id)
        apps = query.all()
        rows: list[dict] = []
        for app in apps:
            candidate = db.get(User, app.candidate_user_id)
            analysis = db.get(GapAnalysis, app.gap_analysis_id) if app.gap_analysis_id else None
            score = float(app.match_score if app.match_score is not None else (analysis.match_score if analysis else 0) or 0)
            rows.append(
                {
                    "candidate_name": candidate.full_name if candidate else "Candidate",
                    "candidate_email": candidate.email if candidate else "",
                    "match_score": score,
                    "stage": app.stage.value,
                    "job_title": job.title if job else None,
                    "summary": analysis.narrative_summary if analysis else "",
                }
            )
        rows.sort(key=lambda item: item["match_score"], reverse=True)
        return rows[:5]

    def _summarise_cv(self, db: Session, recruiter_id: UUID, message: str) -> dict | None:
        cvs = db.query(CandidateCv).order_by(CandidateCv.created_at.desc()).all()
        # Prefer CVs linked to this recruiter's applications.
        linked_ids = {
            app.cv_id
            for app in db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter_id).all()
            if app.cv_id
        }
        candidate_name = None
        name_match = re.search(r"summar(?:y|ise|ize).*?(?:for|of)\s+([A-Za-z][A-Za-z\s'-]{1,60})", message, re.I)
        if name_match:
            candidate_name = name_match.group(1).strip().lower()

        selected = None
        for cv in cvs:
            if linked_ids and cv.id not in linked_ids and cv.uploaded_by != recruiter_id:
                continue
            if candidate_name and candidate_name not in cv.candidate_name.lower():
                continue
            selected = cv
            break
        if selected is None:
            for cv in cvs:
                if cv.uploaded_by == recruiter_id or cv.id in linked_ids:
                    selected = cv
                    break
        if selected is None:
            return None

        profile = selected.parsed_profile or {}
        skills = profile.get("skills") or []
        text = (selected.extracted_text or "")[:500]
        return {
            "candidate_name": selected.candidate_name,
            "skills": skills[:12],
            "years_experience": profile.get("years_experience"),
            "excerpt": text,
        }

    def _list_applications(self, db: Session, recruiter_id: UUID, job: JobSpecification | None) -> list[dict]:
        query = db.query(JobApplication).filter(JobApplication.recruiter_id == recruiter_id)
        if job:
            query = query.filter(JobApplication.job_spec_id == job.id)
        apps = query.order_by(JobApplication.created_at.desc()).limit(10).all()
        rows = []
        for app in apps:
            candidate = db.get(User, app.candidate_user_id)
            rows.append(
                {
                    "candidate_name": candidate.full_name if candidate else "Candidate",
                    "stage": app.stage.value,
                    "match_score": app.match_score,
                }
            )
        return rows

    def _compose_answer(self, message: str, structured: dict, job: JobSpecification | None) -> str:
        parts: list[str] = []
        role = job.title if job else "your open roles"
        if structured.get("matches"):
            top = structured["matches"][0]
            parts.append(
                f"For {role}, the strongest current applicant is {top['candidate_name']} "
                f"with match score {top['match_score']:.0f}/100 ({top['stage']})."
            )
            if len(structured["matches"]) > 1:
                others = ", ".join(
                    f"{item['candidate_name']} ({item['match_score']:.0f})"
                    for item in structured["matches"][1:4]
                )
                parts.append(f"Other ranked candidates: {others}.")
        if structured.get("summary"):
            summary = structured["summary"]
            skills = ", ".join(summary.get("skills") or []) or "skills not extracted"
            parts.append(
                f"CV summary for {summary['candidate_name']}: experience signal "
                f"{summary.get('years_experience') or 'n/a'} years; key skills: {skills}."
            )
        if structured.get("applications") and not structured.get("matches"):
            parts.append(f"Found {len(structured['applications'])} recent applications for {role}.")
        if not parts:
            parts.append("I could not find matching candidate data for that query yet.")
        parts.append(f"Query received: {message}")
        return " ".join(parts)

    def _openai_polish(self, message: str, structured: dict, baseline: str) -> str | None:
        if not settings.openai_api_key:
            logger.info("assistant_agent: no OpenAI API key configured, using deterministic baseline")
            return None
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
                            "content": (
                                "You are a recruiter assistant. Answer using only provided structured data. "
                                "Return JSON with key answer (a single string, never an array or null)."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {"query": message, "structured": structured, "baseline_answer": baseline}
                            ),
                        },
                    ],
                },
                timeout=45.0,
            )
            response.raise_for_status()
            payload = json.loads(response.json()["choices"][0]["message"]["content"])
            return as_text(payload.get("answer"), baseline)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "assistant_agent: OpenAI returned status %s: %s",
                exc.response.status_code,
                exc.response.text[:300],
            )
            return None
        except httpx.HTTPError as exc:
            logger.warning("assistant_agent: OpenAI request failed: %s", exc)
            return None
        except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
            logger.warning("assistant_agent: could not parse OpenAI response: %s", exc)
            return None
