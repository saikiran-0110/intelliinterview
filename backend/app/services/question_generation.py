"""Generate role-specific interview questions from gap analysis results."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CandidateCv,
    GapAnalysis,
    InterviewQuestion,
    InterviewSession,
    JobSpecification,
    QuestionPlan,
    QuestionSource,
)

logger = logging.getLogger(__name__)


def _skill_name(item: dict[str, Any] | str) -> str:
    if isinstance(item, str):
        return item
    return str(item.get("name", "")).strip()


def _build_baseline_questions(
    candidate_name: str,
    job_title: str,
    analysis: GapAnalysis,
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        text: str,
        topic: str,
        question_type: str,
        skill_ref: str | None = None,
        rationale: str | None = None,
    ) -> None:
        key = text.lower().strip()
        if key in seen:
            return
        seen.add(key)
        questions.append(
            {
                "text": text,
                "topic": topic,
                "question_type": question_type,
                "skill_ref": skill_ref,
                "rationale": rationale,
            }
        )

    for item in analysis.gaps or []:
        skill = _skill_name(item)
        if not skill:
            continue
        add(
            text=(
                f"The {job_title} role requires {skill}. Walk us through a project where you used "
                f"{skill}, or how you would ramp up on it for this role."
            ),
            topic=skill,
            question_type="gap_probe",
            skill_ref=skill,
            rationale=f"Required skill '{skill}' was not clearly evidenced in the CV.",
        )

    for item in analysis.partial_matches or []:
        skill = _skill_name(item)
        related = item.get("related_cv_skill") if isinstance(item, dict) else None
        if not skill:
            continue
        related_note = f" (related CV skill: {related})" if related else ""
        add(
            text=(
                f"Your CV suggests related experience{related_note}. How would you apply that "
                f"background to {skill} work expected in the {job_title} role?"
            ),
            topic=skill,
            question_type="partial_probe",
            skill_ref=skill,
            rationale=f"Partial match for '{skill}'{related_note}.",
        )

    for item in (analysis.strong_matches or [])[:3]:
        skill = _skill_name(item)
        if not skill:
            continue
        add(
            text=(
                f"{candidate_name}, you list strong experience with {skill}. Describe a complex "
                f"challenge you solved with {skill} and the trade-offs you considered."
            ),
            topic=skill,
            question_type="depth",
            skill_ref=skill,
            rationale=f"Validate depth of a strong match: {skill}.",
        )

    experience = analysis.experience_analysis or {}
    if experience.get("alignment") in {"partial", "gap", "unknown"}:
        required_years = experience.get("required_years_experience")
        years_note = f" of about {required_years}+ years" if required_years else ""
        add(
            text=(
                f"This {job_title} role expects senior engineering experience{years_note}. "
                f"Tell us about the most complex system you owned end to end and your specific "
                f"responsibilities."
            ),
            topic="experience",
            question_type="experience",
            skill_ref=None,
            rationale="Experience alignment needs interview validation.",
        )

    qualifications = analysis.qualifications_analysis or {}
    missing = qualifications.get("missing_qualifications") or []
    if missing:
        add(
            text=(
                f"The role mentions {', '.join(missing)}. How do your education and professional "
                f"experience compensate for or address these requirements?"
            ),
            topic="qualifications",
            question_type="qualifications",
            skill_ref=None,
            rationale=f"Missing qualifications: {', '.join(missing)}.",
        )

    evidence = analysis.evidence_passages or []
    for passage in evidence[:2]:
        skill = passage.get("skill") if isinstance(passage, dict) else None
        excerpt = passage.get("passage") if isinstance(passage, dict) else None
        if not skill or not excerpt:
            continue
        add(
            text=(
                f"Your CV mentions: \"{excerpt[:180]}...\". Expand on that work and how it "
                f"relates to {skill} expectations for this role."
            ),
            topic=skill,
            question_type="evidence",
            skill_ref=skill,
            rationale="Grounded in a CV evidence passage.",
        )

    if not questions:
        add(
            text=(
                f"Based on the {job_title} requirements, describe a recent technical project and "
                f"how your approach would transfer to this role."
            ),
            topic="role_alignment",
            question_type="general",
            skill_ref=None,
            rationale="Fallback role-alignment question when no specific gaps were detected.",
        )

    add(
        text=(
            f"Imagine you join as {job_title}. In your first 90 days, what technical risks would "
            f"you investigate first and how would you validate them?"
        ),
        topic="problem_solving",
        question_type="scenario",
        skill_ref=None,
        rationale="Role-specific problem-solving scenario.",
    )

    return questions[:12]


def _enhance_with_openai(
    candidate_name: str,
    job_title: str,
    cv_text: str,
    job_text: str,
    analysis: GapAnalysis,
    baseline: list[dict[str, Any]],
    language: str | None = None,
) -> list[dict[str, Any]] | None:
    if not settings.openai_api_key:
        logger.info("question_generation: no OpenAI API key configured, using deterministic baseline")
        return None

    # Part D5: ground each coverage target in the actual retrieved CV passage for
    # that skill (when gap_analysis.py's semantic layer produced one) rather than
    # just the bare skill name, so generated questions reference real CV text.
    passage_by_skill = {
        item.get("skill"): item.get("passage")
        for item in (analysis.evidence_passages or [])
        if isinstance(item, dict) and item.get("skill")
    }
    coverage_targets = [
        {
            "skill_ref": item.get("skill_ref"),
            "topic": item.get("topic"),
            "question_type": item.get("question_type"),
            "why": item.get("rationale"),
            "retrieved_passage": passage_by_skill.get(item.get("skill_ref")),
        }
        for item in baseline
    ]

    prompt = {
        "candidate_name": candidate_name,
        "job_title": job_title,
        "language": language or "en-GB",
        "cv_excerpt": cv_text[:5000],
        "job_excerpt": job_text[:5000],
        "gap_summary": {
            "strong_matches": analysis.strong_matches,
            "partial_matches": analysis.partial_matches,
            "gaps": analysis.gaps,
            "experience_analysis": analysis.experience_analysis,
            "qualifications_analysis": analysis.qualifications_analysis,
            "narrative_summary": analysis.narrative_summary,
        },
        "coverage_targets": coverage_targets,
        "instructions": (
            "Write the question text entirely in the language given as 'language' (a BCP-47 "
            "tag). Skill names, technology names and evidence quotes stay in their original "
            "form - do not translate them. "
            "Write 6 to 10 original interview questions. "
            "coverage_targets lists WHICH skills and question types to cover — it is a "
            "checklist, not wording to copy. Write every question yourself in your own words. "
            "Do NOT use the phrasing 'Walk us through a project where you used X, or how you "
            "would ramp up on it', 'Describe a complex challenge you solved with X', or any "
            "other formulaic template. "
            "Each question must reference something concrete from the CV or job excerpt — a "
            "named project, a specific technology pairing, a stated responsibility — so it "
            "could not have been asked of a different candidate. "
            "For gap skills, ask how the candidate's nearest actual experience would transfer, "
            "naming that experience. "
            "Each coverage_target may carry a retrieved_passage - an actual CV passage "
            "retrieved for that skill. Prefer grounding the question in that passage over "
            "the bare skill name when one is present. "
            "Quote the CV or a retrieved_passage exactly when you quote it, character for "
            "character; never correct its spelling or spacing. "
            "Return JSON with key 'questions': each item has text, topic, question_type "
            "(gap_probe|partial_probe|depth|experience|scenario|evidence|qualifications), "
            "skill_ref (nullable), and rationale."
        ),
    }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "temperature": 0.55,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You generate tailored software engineering interview questions "
                            "from CV and job-specification gap analysis."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        questions = payload.get("questions")
        if not isinstance(questions, list) or not questions:
            return None
        cleaned: list[dict[str, Any]] = []
        for item in questions:
            if not isinstance(item, dict) or not item.get("text"):
                continue
            cleaned.append(
                {
                    "text": str(item["text"]).strip(),
                    "topic": str(item.get("topic") or item.get("skill_ref") or "technical").strip(),
                    "question_type": str(item.get("question_type") or "technical").strip(),
                    "skill_ref": item.get("skill_ref"),
                    "rationale": item.get("rationale"),
                }
            )
        if not cleaned:
            return None

        baseline_texts = {item["text"].strip().lower() for item in baseline}
        copied = [item["text"] for item in cleaned if item["text"].strip().lower() in baseline_texts]
        if copied:
            logger.warning(
                "question_generation: %d generated question(s) matched baseline wording verbatim: %s",
                len(copied),
                copied,
            )
        return cleaned
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "question_generation: OpenAI returned status %s: %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except httpx.HTTPError as exc:
        logger.warning("question_generation: OpenAI request failed: %s", exc)
        return None
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("question_generation: could not parse OpenAI response: %s", exc)
        return None


class QuestionGenerationService:
    def generate_plan(
        self,
        db: Session,
        analysis: GapAnalysis,
        cv: CandidateCv,
        job_spec: JobSpecification,
        recruiter_id: UUID,
        language: str | None = None,
    ) -> tuple[QuestionPlan, list[InterviewQuestion]]:
        # The deterministic baseline below always stays in English - an accepted limitation.
        # `language` is only known when a recruiter passes one explicitly (there is no
        # session yet at plan-generation time); when given, only the OpenAI-enhanced path
        # honours it.
        baseline = _build_baseline_questions(cv.candidate_name, job_spec.title, analysis)
        cv_text = cv.extracted_text or ""
        job_text = job_spec.extracted_text or job_spec.description
        generated = (
            _enhance_with_openai(
                cv.candidate_name, job_spec.title, cv_text, job_text, analysis, baseline, language
            )
            or baseline
        )

        existing_plans = (
            db.query(QuestionPlan)
            .filter(QuestionPlan.gap_analysis_id == analysis.id, QuestionPlan.created_by == recruiter_id)
            .all()
        )
        existing_plan_ids = [existing.id for existing in existing_plans]
        if existing_plan_ids:
            session_in_progress = (
                db.query(InterviewSession)
                .filter(InterviewSession.question_plan_id.in_(existing_plan_ids))
                .first()
            )
            if session_in_progress is not None:
                raise ValueError(
                    "An interview session already exists for this candidate, so the "
                    "question plan can no longer be regenerated."
                )
        for plan in existing_plans:
            db.query(InterviewQuestion).filter(InterviewQuestion.plan_id == plan.id).delete()
            db.delete(plan)
        db.flush()

        plan = QuestionPlan(
            gap_analysis_id=analysis.id,
            title=f"Interview plan: {cv.candidate_name} for {job_spec.title}",
            created_by=recruiter_id,
        )
        db.add(plan)
        db.flush()

        questions: list[InterviewQuestion] = []
        for index, item in enumerate(generated):
            question = InterviewQuestion(
                plan_id=plan.id,
                text=item["text"],
                topic=item["topic"],
                question_type=item.get("question_type") or "technical",
                source=QuestionSource.AI,
                skill_ref=item.get("skill_ref"),
                rationale=item.get("rationale"),
                sort_order=index,
                approved=True,
            )
            db.add(question)
            questions.append(question)

        db.commit()
        db.refresh(plan)
        for question in questions:
            db.refresh(question)
        return plan, questions

    def add_custom_question(
        self,
        db: Session,
        plan: QuestionPlan,
        text: str,
        topic: str,
        skill_ref: str | None = None,
    ) -> InterviewQuestion:
        max_order = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.plan_id == plan.id)
            .count()
        )
        question = InterviewQuestion(
            plan_id=plan.id,
            text=text.strip(),
            topic=topic.strip(),
            question_type="custom",
            source=QuestionSource.RECRUITER,
            skill_ref=skill_ref,
            rationale="Added by recruiter.",
            sort_order=max_order,
            approved=True,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question
