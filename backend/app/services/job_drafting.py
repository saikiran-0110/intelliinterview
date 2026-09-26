"""Draft complete job requisitions from a short recruiter prompt."""

from __future__ import annotations

import json
import logging
import re

import httpx

from app.config import settings
from app.models import EmploymentType, WorkMode

logger = logging.getLogger(__name__)


def _as_money(value: object, fallback: float | None) -> float | None:
    """Coerce a model salary field into a float, handling '£80,000', '80k', commas, and None."""
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return fallback
    text = text.replace("£", "").replace(",", "").replace("$", "").strip()
    match = re.match(r"(\d+(?:\.\d+)?)\s*(k)?", text, re.I)
    if not match:
        return fallback
    number = float(match.group(1))
    if match.group(2):
        number *= 1000
    return number


def _as_int(value: object, fallback: int | None) -> int | None:
    """Coerce a model field into an int, extracting the first integer (handles '5+', '5 years')."""
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"\d+", str(value))
    if not match:
        return fallback
    return int(match.group(0))


def _extract_salary_range(prompt: str) -> tuple[float | None, float | None]:
    pounds = re.findall(r"£\s?(\d{2,3}(?:,\d{3})?|\d{4,6})", prompt)
    values = [float(item.replace(",", "")) for item in pounds]
    if len(values) >= 2:
        return min(values[0], values[1]), max(values[0], values[1])
    if len(values) == 1:
        base = values[0]
        return base, base * 1.15
    # e.g. 60k-80k
    match = re.search(r"(\d{2,3})\s*k\s*[-–to]+\s*(\d{2,3})\s*k", prompt, re.I)
    if match:
        return float(match.group(1)) * 1000, float(match.group(2)) * 1000
    return None, None


def _guess_employment(prompt: str) -> EmploymentType:
    lower = prompt.lower()
    if "intern" in lower:
        return EmploymentType.INTERNSHIP
    if "contract" in lower or "contractor" in lower:
        return EmploymentType.CONTRACT
    if "part time" in lower or "part-time" in lower:
        return EmploymentType.PART_TIME
    return EmploymentType.FULL_TIME


def _guess_work_mode(prompt: str) -> WorkMode:
    lower = prompt.lower()
    if "remote" in lower:
        return WorkMode.REMOTE
    if "on-site" in lower or "onsite" in lower or "office based" in lower:
        return WorkMode.ONSITE
    return WorkMode.HYBRID


def _guess_experience(prompt: str) -> int | None:
    match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", prompt, re.I)
    if match:
        return int(match.group(1))
    lower = prompt.lower()
    if "senior" in lower:
        return 5
    if "mid" in lower:
        return 3
    if "junior" in lower or "graduate" in lower:
        return 1
    return 3


def _guess_title(prompt: str) -> str:
    # Prefer quoted title, else first line / first clause.
    quoted = re.search(r"[\"']([^\"']{3,80})[\"']", prompt)
    if quoted:
        return quoted.group(1).strip()
    first = prompt.strip().split("\n")[0].strip()
    first = re.split(r"[.?!]", first)[0].strip()
    if 3 <= len(first) <= 80:
        return first.title() if first.islower() else first
    return "Software Engineer"


def _baseline_draft(prompt: str) -> dict:
    title = _guess_title(prompt)
    salary_min, salary_max = _extract_salary_range(prompt)
    if salary_min is None:
        salary_min, salary_max = 55000.0, 75000.0
    years = _guess_experience(prompt)
    employment = _guess_employment(prompt)
    work_mode = _guess_work_mode(prompt)
    location = "London, UK"
    loc_match = re.search(
        r"\b(London|Manchester|Birmingham|Leeds|Bristol|Edinburgh|Glasgow|Remote UK|UK)\b",
        prompt,
        re.I,
    )
    if loc_match:
        location = loc_match.group(1)

    department = "Engineering"
    if re.search(r"product", prompt, re.I):
        department = "Product"
    elif re.search(r"data|ml|ai", prompt, re.I):
        department = "Data"
    elif re.search(r"design", prompt, re.I):
        department = "Design"

    description = (
        f"About the role\n"
        f"We are hiring a {title} to join our {department} team. "
        f"This role was drafted from your hiring brief and is ready to refine before publishing.\n\n"
        f"What you will do\n"
        f"- Deliver high-quality software for production systems\n"
        f"- Collaborate with product, design, and engineering partners\n"
        f"- Contribute to code quality, reviews, and technical decisions\n"
        f"- Help improve reliability, performance, and developer experience\n\n"
        f"What we look for\n"
        f"- Around {years}+ years of relevant experience\n"
        f"- Strong fundamentals and practical delivery skills\n"
        f"- Clear communication and ownership mindset\n\n"
        f"Hiring brief from recruiter\n"
        f"{prompt.strip()}\n"
    )
    benefits = (
        "Competitive salary, pension contribution, private healthcare, "
        "25 days holiday plus bank holidays, learning budget, and flexible hybrid working."
    )
    return {
        "title": title[:255],
        "description": description,
        "department": department,
        "location": location,
        "employment_type": employment.value,
        "work_mode": work_mode.value,
        "salary_min_gbp": salary_min,
        "salary_max_gbp": salary_max,
        "years_experience_min": years,
        "benefits": benefits,
        "model_version": "baseline",
    }


def _openai_draft(prompt: str, baseline: dict) -> dict | None:
    if not settings.openai_api_key:
        logger.info("job_drafting: no OpenAI API key configured, using deterministic baseline")
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
                            "You draft UK software hiring job requisitions. "
                            "Return JSON with keys: title, description, department, location, "
                            "employment_type (FULL_TIME|PART_TIME|CONTRACT|INTERNSHIP), "
                            "work_mode (ONSITE|HYBRID|REMOTE), salary_min_gbp, salary_max_gbp, "
                            "years_experience_min, benefits. "
                            "Salaries must be in GBP pounds. Description should be polished and complete. "
                            "salary_min_gbp, salary_max_gbp and years_experience_min must be plain numbers "
                            "with no currency symbols, commas or units (e.g. 80000, not '£80,000' or '80k'). "
                            "If the recruiter's prompt does not state a salary, return null for both salary "
                            "fields — never invent a salary. Keep the recruiter's job title wording if given."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "recruiter_prompt": prompt,
                                "baseline_draft": baseline,
                                "instructions": (
                                    "Enhance the baseline into a ready-to-publish recruitment request. "
                                    "Keep UK context and realistic salary bands in pounds. "
                                    "The baseline_draft's description and benefits are generic "
                                    "placeholder text, not something to copy - write both yourself, "
                                    "grounded in what the recruiter_prompt actually says. For benefits "
                                    "specifically: if the recruiter's prompt mentions any benefits, "
                                    "perks, or compensation details, reflect those specifically; "
                                    "otherwise write a realistic, role-appropriate benefits line in "
                                    "your own words. Do not reuse the baseline's benefits wording."
                                ),
                            }
                        ),
                    },
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["choices"][0]["message"]["content"])
        employment = str(payload.get("employment_type") or baseline["employment_type"]).upper()
        work_mode = str(payload.get("work_mode") or baseline["work_mode"]).upper()
        if employment not in {e.value for e in EmploymentType}:
            employment = baseline["employment_type"]
        if work_mode not in {w.value for w in WorkMode}:
            work_mode = baseline["work_mode"]

        salary_min = _as_money(payload.get("salary_min_gbp"), baseline["salary_min_gbp"])
        salary_max = _as_money(payload.get("salary_max_gbp"), baseline["salary_max_gbp"])
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min

        benefits = str(payload.get("benefits") or baseline["benefits"])
        if benefits.strip().lower() == baseline["benefits"].strip().lower():
            logger.warning(
                "job_drafting: model returned the baseline benefits text verbatim instead of "
                "writing its own"
            )

        return {
            "title": str(payload.get("title") or baseline["title"])[:255],
            "description": str(payload.get("description") or baseline["description"]),
            "department": str(payload.get("department") or baseline["department"]),
            "location": str(payload.get("location") or baseline["location"]),
            "employment_type": employment,
            "work_mode": work_mode,
            "salary_min_gbp": salary_min,
            "salary_max_gbp": salary_max,
            "years_experience_min": _as_int(
                payload.get("years_experience_min"), baseline["years_experience_min"]
            ),
            "benefits": benefits,
            "model_version": settings.openai_model,
        }
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "job_drafting: OpenAI returned status %s: %s", exc.response.status_code, exc.response.text[:300]
        )
        return None
    except httpx.HTTPError as exc:
        logger.warning("job_drafting: OpenAI request failed: %s", exc)
        return None
    except (KeyError, json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
        logger.warning("job_drafting: could not parse OpenAI response: %s", exc)
        return None


class JobDraftingService:
    def draft(self, prompt: str) -> dict:
        cleaned = prompt.strip()
        baseline = _baseline_draft(cleaned)
        return _openai_draft(cleaned, baseline) or baseline
