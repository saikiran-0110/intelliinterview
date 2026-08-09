"""Generate personalised interview preparation packs for candidates."""

from __future__ import annotations

import json
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CandidateCv, GapAnalysis, JobSpecification, PreparationPack
from app.services.gap_analysis import GapAnalysisService


def _baseline_pack(job_title: str, analysis: GapAnalysis) -> dict:
    gaps = []
    for item in analysis.gaps or []:
        name = item.get("name") if isinstance(item, dict) else str(item)
        if name:
            gaps.append(str(name))
    strong = []
    for item in analysis.strong_matches or []:
        name = item.get("name") if isinstance(item, dict) else str(item)
        if name:
            strong.append(str(name))

    focus = gaps[:5] or strong[:3] or ["core technical fundamentals"]
    questions = [
        f"Explain a recent project where you used {focus[0]} and the trade-offs you made.",
        f"How would you approach a typical {job_title} problem involving {focus[0]}?",
        "Walk through how you debug a production issue from detection to resolution.",
        "Describe a time you improved system performance and how you measured success.",
    ]
    if len(focus) > 1:
        questions.append(f"Compare {focus[0]} and {focus[1]} for this role and when you would choose each.")
    guidance = (
        f"Before your {job_title} interview, prepare STAR-style examples for your strongest skills "
        f"({', '.join(strong[:3]) if strong else 'your core stack'}) and rehearse clear explanations "
        f"for weaker areas ({', '.join(gaps[:3]) if gaps else 'system design fundamentals'})."
    )
    return {
        "practice_questions": questions,
        "guidance": guidance,
        "focus_areas": focus,
        "model_version": "baseline",
    }


def _openai_pack(job_title: str, cv_text: str, job_text: str, baseline: dict) -> dict | None:
    if not settings.openai_api_key:
        return None
    prompt = {
        "job_title": job_title,
        "cv_excerpt": cv_text[:3500],
        "job_excerpt": job_text[:3500],
        "baseline": baseline,
        "instructions": (
            "Create candidate interview preparation content. Return JSON with keys: "
            "practice_questions (array of 5 strings), guidance (string), focus_areas (string array)."
        ),
    }
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.4,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "You create concise software interview preparation packs for candidates.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["choices"][0]["message"]["content"])
        return {
            "practice_questions": payload.get("practice_questions") or baseline["practice_questions"],
            "guidance": payload.get("guidance") or baseline["guidance"],
            "focus_areas": payload.get("focus_areas") or baseline["focus_areas"],
            "model_version": settings.openai_model,
        }
    except (httpx.HTTPError, KeyError, json.JSONDecodeError, IndexError, TypeError):
        return None


class PreparationService:
    def __init__(self) -> None:
        self.gap_service = GapAnalysisService()

    def generate(
        self,
        db: Session,
        *,
        candidate_user_id: UUID,
        cv: CandidateCv,
        job: JobSpecification,
    ) -> PreparationPack:
        owner_id = job.created_by or candidate_user_id
        analysis = (
            db.query(GapAnalysis)
            .filter(GapAnalysis.cv_id == cv.id, GapAnalysis.job_spec_id == job.id)
            .order_by(GapAnalysis.created_at.desc())
            .first()
        )
        if analysis is None:
            analysis = self.gap_service.analyse(db, cv, job, owner_id)

        baseline = _baseline_pack(job.title, analysis)
        polished = _openai_pack(
            job.title,
            cv.extracted_text or "",
            job.extracted_text or job.description,
            baseline,
        ) or baseline

        pack = PreparationPack(
            candidate_user_id=candidate_user_id,
            cv_id=cv.id,
            job_spec_id=job.id,
            practice_questions=polished["practice_questions"],
            guidance=polished["guidance"],
            focus_areas=polished["focus_areas"],
            model_version=polished["model_version"],
        )
        db.add(pack)
        db.commit()
        db.refresh(pack)
        return pack

    def list_for_candidate(self, db: Session, candidate_user_id: UUID) -> list[PreparationPack]:
        return (
            db.query(PreparationPack)
            .filter(PreparationPack.candidate_user_id == candidate_user_id)
            .order_by(PreparationPack.created_at.desc())
            .all()
        )
