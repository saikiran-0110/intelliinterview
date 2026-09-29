"""Rank applicants against a job specification using gap analysis scores."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CandidateCv, GapAnalysis, JobApplication, JobSpecification, PipelineStage, User
from app.services.gap_analysis import GapAnalysisService


def _skill_names(items: list) -> list[str]:
    names: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        else:
            name = str(item).strip()
        if name:
            names.append(name)
    return names


def _plain_language(score: float, strong: list[str], gaps: list[str]) -> str:
    if score >= 75:
        level = "strong overall match"
    elif score >= 55:
        level = "moderate match with some gaps"
    else:
        level = "weak match against the current role requirements"
    strong_text = ", ".join(strong[:4]) if strong else "limited confirmed skill overlap"
    gap_text = ", ".join(gaps[:4]) if gaps else "no major skill gaps flagged"
    return (
        f"This candidate is a {level} (score {score:.0f}/100). "
        f"Strong areas include {strong_text}. Gaps to probe: {gap_text}."
    )


READY_TO_SHORTLIST = {PipelineStage.APPLIED, PipelineStage.SCREENING}


class RankingService:
    def __init__(self) -> None:
        self.gap_service = GapAnalysisService()

    def rank_for_job(self, db: Session, job_spec: JobSpecification, recruiter_id: UUID) -> list[dict]:
        applications = (
            db.query(JobApplication)
            .filter(JobApplication.job_spec_id == job_spec.id, JobApplication.recruiter_id == recruiter_id)
            .all()
        )
        ranked: list[dict] = []

        for application in applications:
            if application.cv_id is None:
                continue
            # Keep ranking focused on candidates still awaiting shortlist decisions.
            if application.stage not in READY_TO_SHORTLIST:
                continue
            cv = db.get(CandidateCv, application.cv_id)
            if cv is None:
                continue

            analysis = None
            if application.gap_analysis_id:
                analysis = db.get(GapAnalysis, application.gap_analysis_id)
            if analysis is None:
                analysis = (
                    db.query(GapAnalysis)
                    .filter(GapAnalysis.cv_id == cv.id, GapAnalysis.job_spec_id == job_spec.id)
                    .order_by(GapAnalysis.created_at.desc())
                    .first()
                )
            if analysis is None:
                analysis = self.gap_service.analyse(db, cv, job_spec, recruiter_id)
            if application.gap_analysis_id != analysis.id:
                application.gap_analysis_id = analysis.id
                application.match_score = analysis.match_score
                db.add(application)
                db.commit()

            candidate = db.get(User, application.candidate_user_id)
            strong = _skill_names(analysis.strong_matches)
            partial = _skill_names(analysis.partial_matches)
            gaps = _skill_names(analysis.gaps)
            score = float(analysis.match_score or 0)
            ranked.append(
                {
                    "application_id": application.id,
                    "candidate_user_id": application.candidate_user_id,
                    "candidate_name": candidate.full_name if candidate else cv.candidate_name,
                    "candidate_email": candidate.email if candidate else None,
                    "cv_id": cv.id,
                    "gap_analysis_id": analysis.id,
                    "match_score": score,
                    "stage": application.stage,
                    "strong_matches": strong,
                    "partial_matches": partial,
                    "gaps": gaps,
                    "narrative_summary": analysis.narrative_summary or "",
                    "plain_language_breakdown": _plain_language(score, strong, gaps),
                }
            )

        ranked.sort(key=lambda item: item["match_score"], reverse=True)
        return ranked
