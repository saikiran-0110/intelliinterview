"""Generate personalised interview preparation packs for candidates."""

from __future__ import annotations

import json
import re
from uuid import UUID, uuid4

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CandidateCv, GapAnalysis, JobSpecification, PreparationPack
from app.services.gap_analysis import GapAnalysisService


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:40] or str(uuid4())[:8]


def _normalize_questions(raw: list) -> list[dict]:
    questions: list[dict] = []
    for index, item in enumerate(raw or []):
        if isinstance(item, dict):
            text = str(item.get("question") or item.get("text") or "").strip()
            if not text:
                continue
            qid = str(item.get("id") or f"q-{index + 1}-{_slug(text)[:18]}")
            questions.append(
                {
                    "id": qid,
                    "question": text,
                    "difficulty": str(item.get("difficulty") or "intermediate"),
                    "topic": str(item.get("topic") or "general"),
                    "talking_points": [
                        str(point).strip()
                        for point in (item.get("talking_points") or [])
                        if str(point).strip()
                    ][:5],
                    "technical_context": str(item.get("technical_context") or "").strip(),
                }
            )
        else:
            text = str(item).strip()
            if not text:
                continue
            questions.append(
                {
                    "id": f"q-{index + 1}-{_slug(text)[:18]}",
                    "question": text,
                    "difficulty": "intermediate",
                    "topic": "general",
                    "talking_points": [],
                    "technical_context": "",
                }
            )
    return questions


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
    primary = focus[0]
    secondary = focus[1] if len(focus) > 1 else "system design"

    questions = [
        {
            "id": f"q-1-{_slug(primary)}",
            "question": f"Explain a recent project where you used {primary} and the trade-offs you made.",
            "difficulty": "intermediate",
            "topic": primary,
            "talking_points": [
                "Describe the business problem and constraints",
                "Explain architecture choices and rejected alternatives",
                "Share metrics that proved the outcome",
            ],
            "technical_context": (
                f"Interviewers often probe depth on {primary}: APIs, failure modes, "
                "observability, and how you validated correctness under load."
            ),
        },
        {
            "id": f"q-2-{_slug(job_title)}",
            "question": f"How would you approach a typical {job_title} problem involving {primary}?",
            "difficulty": "advanced",
            "topic": primary,
            "talking_points": [
                "Clarify requirements and SLAs",
                "Outline design, data flow, and edge cases",
                "Call out testing and rollout strategy",
            ],
            "technical_context": (
                f"Structure your answer as requirements → design → risks → verification. "
                f"Tie decisions back to {job_title} responsibilities."
            ),
        },
        {
            "id": "q-3-debugging",
            "question": "Walk through how you debug a production issue from detection to resolution.",
            "difficulty": "intermediate",
            "topic": "reliability",
            "talking_points": [
                "Triage signals (logs, metrics, traces, alerts)",
                "Form hypotheses and bisect the fault domain",
                "Mitigate impact, then permanently fix and document",
            ],
            "technical_context": (
                "Be ready to discuss incident severity, communication, blameless postmortems, "
                "and how you prevent recurrence."
            ),
        },
        {
            "id": "q-4-performance",
            "question": "Describe a time you improved system performance and how you measured success.",
            "difficulty": "advanced",
            "topic": "performance",
            "talking_points": [
                "Baseline before change",
                "Identify bottleneck with evidence",
                "Quantify after-state improvement",
            ],
            "technical_context": (
                "Mention profiling tools, latency percentiles (p50/p95/p99), throughput, "
                "and cost/complexity trade-offs."
            ),
        },
        {
            "id": f"q-5-{_slug(secondary)}",
            "question": f"Compare {primary} and {secondary} for this role and when you would choose each.",
            "difficulty": "advanced",
            "topic": secondary,
            "talking_points": [
                "Decision criteria (scale, team skills, latency, ops cost)",
                "Concrete scenario preferring each option",
                "Migration or coexistence strategy",
            ],
            "technical_context": (
                f"Show engineering judgment: strengths/limits of {primary} vs {secondary}, "
                "and how the choice affects maintainability."
            ),
        },
    ]

    study_modules = []
    for skill in focus[:4]:
        study_modules.append(
            {
                "id": f"mod-{_slug(skill)}",
                "title": f"Deep dive: {skill}",
                "summary": f"Build interview-ready depth on {skill} for a {job_title} conversation.",
                "technical_details": (
                    f"Review core concepts of {skill}, common failure modes, and at least one "
                    f"end-to-end example you can whiteboard. Prepare one production story and one "
                    f"design question answer that uses {skill} as the primary lever."
                ),
                "topic": skill,
                "estimated_minutes": 45,
            }
        )
    study_modules.append(
        {
            "id": "mod-system-design",
            "title": "System design rehearsal",
            "summary": f"Practice a 20-minute design for a service relevant to {job_title}.",
            "technical_details": (
                "Cover requirements, high-level architecture, data model, APIs, scaling, "
                "consistency, caching, and failure handling. Time-box yourself and leave 3 minutes "
                "for trade-off discussion."
            ),
            "topic": "system design",
            "estimated_minutes": 35,
        }
    )

    checklist_items = [
        {
            "id": "chk-star-strong",
            "label": f"Prepare STAR stories for strengths ({', '.join(strong[:3]) if strong else 'core stack'})",
            "category": "storytelling",
            "technical_hint": "Quantify impact with metrics and mention technical decisions explicitly.",
        },
        {
            "id": "chk-gap-study",
            "label": f"Study gap topics ({', '.join(gaps[:3]) if gaps else 'fundamentals'}) with notes",
            "category": "technical study",
            "technical_hint": "Write a one-page cheat sheet: concepts, commands/APIs, pitfalls, and an example.",
        },
        {
            "id": "chk-whiteboard",
            "label": f"Whiteboard a {primary} design for 15 minutes",
            "category": "practice",
            "technical_hint": "Narrate assumptions, draw components, and state how you would test it.",
        },
        {
            "id": "chk-questions",
            "label": "Draft 3 thoughtful questions for the interviewer about the role/team",
            "category": "interview craft",
            "technical_hint": "Ask about architecture ownership, on-call, delivery cadence, and success metrics.",
        },
        {
            "id": "chk-mock",
            "label": "Complete one timed mock answer for each practice question",
            "category": "practice",
            "technical_hint": "Record yourself or use a timer; refine clarity and technical depth on a second pass.",
        },
    ]

    guidance = (
        f"Before your {job_title} interview, prepare STAR-style examples for your strongest skills "
        f"({', '.join(strong[:3]) if strong else 'your core stack'}) and rehearse clear explanations "
        f"for weaker areas ({', '.join(gaps[:3]) if gaps else 'system design fundamentals'}). "
        f"Work through the study modules and mark checklist items complete as you go."
    )
    return {
        "practice_questions": questions,
        "guidance": guidance,
        "focus_areas": focus,
        "study_modules": study_modules,
        "checklist_items": checklist_items,
        "model_version": "baseline-advanced",
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
            "Create an advanced candidate interview preparation pack. Return JSON with keys: "
            "practice_questions (array of objects with id, question, difficulty, topic, "
            "talking_points array, technical_context), guidance (string), focus_areas (string array), "
            "study_modules (array of objects with id, title, summary, technical_details, topic, "
            "estimated_minutes), checklist_items (array of objects with id, label, category, "
            "technical_hint). Make content specific and technical, not generic."
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
                        "content": (
                            "You create advanced software interview preparation packs with "
                            "technical depth, study modules, and actionable checklists."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["choices"][0]["message"]["content"])
        return {
            "practice_questions": _normalize_questions(
                payload.get("practice_questions") or baseline["practice_questions"]
            ),
            "guidance": payload.get("guidance") or baseline["guidance"],
            "focus_areas": payload.get("focus_areas") or baseline["focus_areas"],
            "study_modules": payload.get("study_modules") or baseline["study_modules"],
            "checklist_items": payload.get("checklist_items") or baseline["checklist_items"],
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
            practice_questions=_normalize_questions(polished["practice_questions"]),
            guidance=polished["guidance"],
            focus_areas=polished["focus_areas"],
            study_modules=polished.get("study_modules") or [],
            checklist_items=polished.get("checklist_items") or [],
            completed_item_ids=[],
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

    def get_owned(self, db: Session, pack_id: UUID, candidate_user_id: UUID) -> PreparationPack | None:
        return (
            db.query(PreparationPack)
            .filter(
                PreparationPack.id == pack_id,
                PreparationPack.candidate_user_id == candidate_user_id,
            )
            .first()
        )

    def delete_pack(self, db: Session, pack: PreparationPack) -> None:
        db.delete(pack)
        db.commit()

    def toggle_progress(
        self,
        db: Session,
        pack: PreparationPack,
        *,
        item_id: str,
        completed: bool,
    ) -> PreparationPack:
        current = [str(value) for value in (pack.completed_item_ids or [])]
        if completed and item_id not in current:
            current.append(item_id)
        if not completed and item_id in current:
            current = [value for value in current if value != item_id]
        pack.completed_item_ids = current
        db.add(pack)
        db.commit()
        db.refresh(pack)
        return pack
