from app.models import EmploymentType, WorkMode
from app.services.job_drafting import (
    JobDraftingService,
    _baseline_draft,
    _extract_salary_range,
    _guess_employment,
    _guess_experience,
    _guess_title,
    _guess_work_mode,
)


def test_extract_salary_range_from_pounds_and_k_notation():
    pounds = "salary \u00a380,000-\u00a3100,000"
    assert _extract_salary_range(pounds) == (80000.0, 100000.0)
    assert _extract_salary_range("60k-80k") == (60000.0, 80000.0)
    assert _extract_salary_range("no salary") == (None, None)


def test_guess_employment_and_work_mode():
    assert _guess_employment("summer intern role") == EmploymentType.INTERNSHIP
    assert _guess_employment("6 month contractor") == EmploymentType.CONTRACT
    assert _guess_employment("part-time engineer") == EmploymentType.PART_TIME
    assert _guess_employment("permanent hire") == EmploymentType.FULL_TIME
    assert _guess_work_mode("fully remote UK") == WorkMode.REMOTE
    assert _guess_work_mode("office based in London") == WorkMode.ONSITE
    assert _guess_work_mode("hybrid in Manchester") == WorkMode.HYBRID


def test_guess_experience_and_title():
    assert _guess_experience("5+ years Kubernetes") == 5
    assert _guess_experience("senior platform engineer") == 5
    assert _guess_experience("mid engineer") == 3
    assert _guess_experience("graduate software engineer") == 1
    assert _guess_title("'Platform Engineer' in London") == "Platform Engineer"
    assert _guess_title("ab") == "Software Engineer"


def test_baseline_draft_and_service_without_openai():
    prompt = "Senior Platform Engineer in Manchester, contract, 5+ years Python, salary 80k-100k"
    draft = _baseline_draft(prompt)
    assert draft["title"]
    assert draft["location"] == "Manchester"
    assert draft["employment_type"] == EmploymentType.CONTRACT.value
    assert draft["salary_min_gbp"] == 80000.0
    assert draft["salary_max_gbp"] == 100000.0
    assert draft["years_experience_min"] == 5
    assert "Hiring brief from recruiter" in draft["description"]

    service = JobDraftingService()
    result = service.draft(prompt)
   # assert result["model_version"] == "baseline"
    assert result["title"] == draft["title"]
