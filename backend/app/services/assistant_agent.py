"""Recruiter AI assistant with tool-style queries over candidate data (no LangChain dependency)."""

from __future__ import annotations

import json
import re
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CandidateCv, GapAnalysis, JobApplication, JobSpecification, User


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
                                "Return JSON with key answer."
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
            answer = payload.get("answer")
            return str(answer).strip() if answer else None
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, IndexError, TypeError):
            return None
