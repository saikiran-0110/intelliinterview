"""Structured gap analysis between a parsed CV profile and job requirements."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CandidateCv, GapAnalysis, JobSpecification
from app.services.llm_json import as_dict_list, as_text
from app.services.skill_catalog import (
    compare_skills,
    extract_evidence_passage,
    parse_cv_profile,
    parse_job_requirements,
)

logger = logging.getLogger(__name__)


def _build_experience_analysis(cv_profile: dict[str, Any], job_requirements: dict[str, Any]) -> dict[str, Any]:
    cv_years = cv_profile.get("years_experience")
    required_years = job_requirements.get("years_experience_required")
    cv_seniority = cv_profile.get("seniority")
    required_seniority = job_requirements.get("seniority_required")

    alignment = "unknown"
    notes: list[str] = []

    if cv_years is not None and required_years is not None:
        if cv_years >= required_years:
            alignment = "strong"
            notes.append(f"Candidate reports {cv_years} years of experience against {required_years}+ required.")
        elif cv_years >= max(required_years - 1, 1):
            alignment = "partial"
            notes.append(
                f"Candidate reports {cv_years} years of experience, slightly below the {required_years}+ requirement."
            )
        else:
            alignment = "gap"
            notes.append(
                f"Candidate reports {cv_years} years of experience, below the {required_years}+ requirement."
            )
    elif cv_years is not None:
        notes.append(f"Candidate reports {cv_years} years of experience.")
    elif required_years is not None:
        notes.append(f"Role expects around {required_years}+ years of experience but none was detected in the CV.")

    if cv_seniority and required_seniority:
        if cv_seniority == required_seniority:
            notes.append(f"Seniority level '{cv_seniority}' aligns with the role.")
        elif cv_seniority == "mid" and required_seniority == "senior":
            alignment = "partial" if alignment != "gap" else alignment
            notes.append("Candidate appears mid-level while the role targets senior experience.")
        elif cv_seniority == "junior" and required_seniority in {"mid", "senior"}:
            alignment = "gap"
            notes.append("Candidate appears junior relative to the seniority implied by the job specification.")
        else:
            notes.append(f"Seniority signal in CV: {cv_seniority}. Role signal: {required_seniority}.")

    return {
        "alignment": alignment,
        "cv_years_experience": cv_years,
        "required_years_experience": required_years,
        "cv_seniority": cv_seniority,
        "required_seniority": required_seniority,
        "notes": notes,
    }


def _build_qualifications_analysis(cv_profile: dict[str, Any], job_requirements: dict[str, Any]) -> dict[str, Any]:
    cv_quals = set(cv_profile.get("qualifications", []))
    job_quals = set(job_requirements.get("qualifications_required", []))

    matched = sorted(cv_quals & job_quals)
    missing = sorted(job_quals - cv_quals)
    additional = sorted(cv_quals - job_quals)

    if job_quals:
        if not missing:
            alignment = "strong"
        elif matched:
            alignment = "partial"
        else:
            alignment = "gap"
    else:
        alignment = "not_specified"

    return {
        "alignment": alignment,
        "matched_qualifications": matched,
        "missing_qualifications": missing,
        "additional_qualifications": additional,
        "notes": [
            "Qualification requirements are explicit in the job specification."
            if job_quals
            else "No explicit qualification requirements were detected in the job specification."
        ],
    }


def _build_evidence_passages(cv_text: str, matches: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    passages: list[dict[str, str]] = []
    for group, match_type in (
        (matches["strong"], "strong"),
        (matches["partial"], "partial"),
        (matches["gaps"], "gap"),
    ):
        for item in group:
            skill = item["name"]
            passage = extract_evidence_passage(cv_text, skill)
            if passage:
                passages.append(
                    {
                        "skill": skill,
                        "match_type": match_type,
                        "passage": passage,
                    }
                )
    return passages[:12]


def _calculate_match_score(
    strong_count: int, partial_count: int, gap_count: int, experience_alignment: str
) -> float:
    total = strong_count + partial_count + gap_count
    if total == 0:
        base = 50.0
    else:
        base = ((strong_count * 1.0) + (partial_count * 0.5)) / total * 100

    if experience_alignment == "strong":
        base = min(100.0, base + 5)
    elif experience_alignment == "gap":
        base = max(0.0, base - 10)
    return round(base, 1)


def _build_narrative_summary(
    candidate_name: str,
    job_title: str,
    matches: dict[str, list[dict[str, Any]]],
    experience: dict[str, Any],
    qualifications: dict[str, Any],
) -> str:
    strong_names = ", ".join(item["name"] for item in matches["strong"]) or "none detected"
    partial_names = ", ".join(item["name"] for item in matches["partial"]) or "none detected"
    gap_names = ", ".join(item["name"] for item in matches["gaps"]) or "none detected"
    experience_note = experience["notes"][0] if experience.get("notes") else "Experience signals were limited."
    qualification_note = (
        f"Matched qualifications: {', '.join(qualifications.get('matched_qualifications', [])) or 'none'}."
    )

    return (
        f"{candidate_name} was compared against the {job_title} role. "
        f"Strong skill matches include {strong_names}. "
        f"Partial matches include {partial_names}. "
        f"Gaps to probe in interview include {gap_names}. "
        f"{experience_note} {qualification_note}"
    )


def _enhance_with_openai(
    candidate_name: str,
    job_title: str,
    cv_text: str,
    job_text: str,
    baseline: dict[str, Any],
) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        logger.info("gap_analysis: no OpenAI API key configured, using deterministic baseline")
        return None

    prompt = {
        "candidate_name": candidate_name,
        "job_title": job_title,
        "cv_excerpt": cv_text[:6000],
        "job_excerpt": job_text[:6000],
        "baseline_analysis": baseline,
        "instructions": (
            "Return JSON with keys strong_matches, partial_matches, gaps (arrays of "
            "{name, rationale}), experience_analysis {alignment, notes}, "
            "qualifications_analysis {alignment, notes, matched_qualifications, missing_qualifications}, "
            "narrative_summary (string). Ground every point in the provided documents only. "
            "Every array field MUST be a JSON array of strings or objects as specified, never a "
            "single concatenated string or null."
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
                        "content": "You analyse software engineering CVs against job specifications.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "gap_analysis: OpenAI returned status %s: %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except httpx.HTTPError as exc:
        logger.warning("gap_analysis: OpenAI request failed: %s", exc)
        return None
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("gap_analysis: could not parse OpenAI response: %s", exc)
        return None


class GapAnalysisService:
    def analyse(
        self,
        db: Session,
        cv: CandidateCv,
        job_spec: JobSpecification,
        recruiter_id: UUID,
    ) -> GapAnalysis:
        cv_text = cv.extracted_text or ""
        job_text = job_spec.extracted_text or job_spec.description

        cv_profile = cv.parsed_profile or parse_cv_profile(cv_text)
        job_requirements = job_spec.parsed_requirements or parse_job_requirements(job_text)

        cv.parsed_profile = cv_profile
        job_spec.parsed_requirements = job_requirements

        matches = compare_skills(cv_profile.get("skills", []), job_requirements.get("required_skills", []))
        experience = _build_experience_analysis(cv_profile, job_requirements)
        qualifications = _build_qualifications_analysis(cv_profile, job_requirements)
        evidence = _build_evidence_passages(cv_text, matches)
        narrative = _build_narrative_summary(cv.candidate_name, job_spec.title, matches, experience, qualifications)
        match_score = _calculate_match_score(
            len(matches["strong"]),
            len(matches["partial"]),
            len(matches["gaps"]),
            experience.get("alignment", "unknown"),
        )

        baseline = {
            "strong_matches": matches["strong"],
            "partial_matches": matches["partial"],
            "gaps": matches["gaps"],
            "experience_analysis": experience,
            "qualifications_analysis": qualifications,
            "narrative_summary": narrative,
        }

        enhanced = _enhance_with_openai(cv.candidate_name, job_spec.title, cv_text, job_text, baseline)
        if enhanced:
            # match_score is deliberately NOT recomputed here: it is the number a recruiter
            # acts on, so it must stay derived only from the deterministic skill-catalogue
            # classification computed above. The model may still reclassify the displayed
            # skill lists and rewrite the narrative, but that must never change the score.
            matches["strong"] = as_dict_list(enhanced.get("strong_matches"), matches["strong"])
            matches["partial"] = as_dict_list(enhanced.get("partial_matches"), matches["partial"])
            matches["gaps"] = as_dict_list(enhanced.get("gaps"), matches["gaps"])
            enhanced_experience = enhanced.get("experience_analysis")
            if isinstance(enhanced_experience, dict):
                experience = enhanced_experience
            enhanced_qualifications = enhanced.get("qualifications_analysis")
            if isinstance(enhanced_qualifications, dict):
                qualifications = enhanced_qualifications
            narrative = as_text(enhanced.get("narrative_summary"), narrative)

        analysis = GapAnalysis(
            cv_id=cv.id,
            job_spec_id=job_spec.id,
            strong_matches=matches["strong"],
            partial_matches=matches["partial"],
            gaps=matches["gaps"],
            experience_analysis=experience,
            qualifications_analysis=qualifications,
            evidence_passages=evidence,
            narrative_summary=narrative,
            match_score=match_score,
            created_by=recruiter_id,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
