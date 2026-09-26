"""Technology skill catalogue and text extraction helpers for CV and job-spec analysis."""

from __future__ import annotations

import re
from typing import Any

TECH_SKILLS: dict[str, list[str]] = {
    "python": ["python", "django", "flask"],
    "fastapi": ["fastapi"],
    "java": ["java", "spring", "spring boot", "hibernate"],
    "javascript": ["javascript", "js", "node.js", "nodejs", "express"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs", "next.js", "nextjs"],
    "angular": ["angular"],
    "vue": ["vue", "vue.js", "vuejs", "nuxt"],
    "csharp": ["c#", "csharp", ".net", "asp.net"],
    "go": ["golang", "go"],
    "rust": ["rust"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "postgresql": ["postgresql", "postgres", "pgvector"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "docker": ["docker", "container"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "git": ["git", "github", "gitlab"],
    "ci/cd": ["ci/cd", "jenkins", "github actions", "gitlab ci"],
    "rest": ["rest", "restful", "rest api"],
    "graphql": ["graphql"],
    "microservices": ["microservices", "microservice"],
    "agile": ["agile", "scrum", "kanban"],
    "testing": ["pytest", "junit", "unit test", "integration test", "tdd"],
    "machine learning": ["machine learning", "ml", "deep learning", "tensorflow", "pytorch"],
    "system design": ["system design", "architecture", "distributed systems"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "tailwind", "bootstrap"],
    "sql": ["sql", "t-sql", "pl/sql"],
    "linux": ["linux", "unix", "bash"],
    "security": ["owasp", "jwt", "oauth", "security"],
}

RELATED_SKILLS: dict[str, set[str]] = {
    "react": {"javascript", "typescript", "html", "css", "rest"},
    "angular": {"typescript", "javascript", "html", "css", "rest"},
    "vue": {"javascript", "typescript", "html", "css", "rest"},
    "fastapi": {"python", "rest", "postgresql", "docker"},
    "django": {"python", "postgresql", "rest"},
    "spring": {"java", "sql", "rest", "microservices"},
    "node.js": {"javascript", "typescript", "rest", "mongodb", "postgresql"},
    "kubernetes": {"docker", "aws", "azure", "gcp", "ci/cd"},
    "machine learning": {"python", "sql"},
    "system design": {"microservices", "rest", "sql", "docker", "kubernetes"},
}

QUALIFICATION_PATTERNS = [
    r"\b(bsc|b\.s\.|bachelor(?:'s)?(?:\s+of\s+(?:science|engineering|computer science))?)\b",
    r"\b(msc|m\.s\.|master(?:'s)?(?:\s+of\s+(?:science|engineering|computer science))?)\b",
    r"\b(phd|ph\.d\.|doctorate)\b",
    r"\b(beng|b\.eng\.)\b",
    r"\b(meng|m\.eng\.)\b",
    r"\b(diploma|hnd|foundation degree)\b",
    r"\b(certification|certified)\b",
]

EXPERIENCE_PATTERN = re.compile(
    r"(\d{1,2})\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?",
    re.IGNORECASE,
)

SENIORITY_KEYWORDS = {
    "junior": ["junior", "graduate", "entry level", "entry-level", "intern"],
    "mid": ["mid level", "mid-level", "intermediate"],
    "senior": ["senior", "lead", "principal", "staff"],
}


def _normalize(text: str) -> str:
    return f" {text.lower()} "


def _alias_matches(alias: str, normalized_text: str) -> bool:
    """Whole-word match for plain alphanumeric aliases, so e.g. "ts" matches standalone
    "TS" but not inside "tests" or "reports", regardless of whether it's next to a space,
    a comma, a parenthesis, a slash, or a semicolon. Aliases containing other characters
    (c#, .net, node.js, ci/cd, t-sql, "spring boot", ...) are already distinctive enough
    and use a plain substring check, since word-boundary regex doesn't apply cleanly to
    punctuation-bearing or multi-word tokens."""
    if alias.isalnum():
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return alias in normalized_text


def extract_skills(text: str) -> list[str]:
    normalized = _normalize(text)
    found: list[str] = []
    for skill, aliases in TECH_SKILLS.items():
        if any(_alias_matches(alias, normalized) for alias in aliases):
            found.append(skill)
    return sorted(set(found))


def extract_years_experience(text: str) -> int | None:
    matches = EXPERIENCE_PATTERN.findall(text.lower())
    if not matches:
        return None
    return max(int(value) for value in matches)


def extract_seniority(text: str) -> str | None:
    lowered = text.lower()
    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return level
    return None


def extract_qualifications(text: str) -> list[str]:
    lowered = text.lower()
    results: list[str] = []
    labels = [
        ("Bachelor's degree", QUALIFICATION_PATTERNS[0]),
        ("Master's degree", QUALIFICATION_PATTERNS[1]),
        ("Doctorate", QUALIFICATION_PATTERNS[2]),
        ("Engineering degree", QUALIFICATION_PATTERNS[3]),
        ("Master of Engineering", QUALIFICATION_PATTERNS[4]),
        ("Diploma", QUALIFICATION_PATTERNS[5]),
        ("Certification", QUALIFICATION_PATTERNS[6]),
    ]
    for label, pattern in labels:
        if re.search(pattern, lowered):
            results.append(label)
    return results


def extract_evidence_passage(text: str, keyword: str, window: int = 120) -> str | None:
    lowered = text.lower()
    keyword_lower = keyword.lower()
    index = lowered.find(keyword_lower)
    if index == -1:
        for alias in TECH_SKILLS.get(keyword, [keyword]):
            index = lowered.find(alias)
            if index != -1:
                break
    if index == -1:
        return None
    start = max(0, index - window)
    end = min(len(text), index + len(keyword) + window)
    snippet = text[start:end].strip()
    return " ".join(snippet.split())


def parse_cv_profile(text: str) -> dict[str, Any]:
    return {
        "skills": extract_skills(text),
        "years_experience": extract_years_experience(text),
        "seniority": extract_seniority(text),
        "qualifications": extract_qualifications(text),
    }


def parse_job_requirements(text: str) -> dict[str, Any]:
    return {
        "required_skills": extract_skills(text),
        "years_experience_required": extract_years_experience(text),
        "seniority_required": extract_seniority(text),
        "qualifications_required": extract_qualifications(text),
    }


def _is_partial_match(cv_skill: str, job_skill: str) -> bool:
    if cv_skill == job_skill:
        return False
    related_to_job = RELATED_SKILLS.get(job_skill, set())
    related_to_cv = RELATED_SKILLS.get(cv_skill, set())
    return job_skill in related_to_cv or cv_skill in related_to_job


def compare_skills(cv_skills: list[str], job_skills: list[str]) -> dict[str, list[dict[str, Any]]]:
    cv_set = set(cv_skills)
    job_set = set(job_skills)

    strong: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    matched_job_skills: set[str] = set()

    for skill in sorted(job_set):
        if skill in cv_set:
            strong.append({"name": skill, "category": "skill"})
            matched_job_skills.add(skill)

    for job_skill in sorted(job_set - matched_job_skills):
        partial_cv = next((cv for cv in cv_set if _is_partial_match(cv, job_skill)), None)
        if partial_cv:
            partial.append(
                {
                    "name": job_skill,
                    "category": "skill",
                    "related_cv_skill": partial_cv,
                }
            )
            matched_job_skills.add(job_skill)

    for job_skill in sorted(job_set - matched_job_skills):
        gaps.append({"name": job_skill, "category": "skill"})

    return {"strong": strong, "partial": partial, "gaps": gaps}
