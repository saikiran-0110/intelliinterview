import json

from app.models import EmploymentType, WorkMode
from app.services import job_drafting as job_drafting_module
from app.services.job_drafting import (
    JobDraftingService,
    _as_int,
    _as_money,
    _baseline_draft,
    _extract_salary_range,
    _guess_employment,
    _guess_experience,
    _guess_title,
    _guess_work_mode,
)


class _FakeResponse:
    def __init__(self, content: dict):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": json.dumps(self._content)}}]}


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
    assert result["model_version"] == "baseline"
    assert result["title"] == draft["title"]


def test_as_money_handles_currency_commas_and_k_suffix():
    assert _as_money("£80,000", None) == 80000.0
    assert _as_money("80k", None) == 80000.0
    assert _as_money(80000, None) == 80000.0
    assert _as_money(80000.5, None) == 80000.5


def test_as_money_none_and_unusable_return_fallback():
    assert _as_money(None, 55000.0) == 55000.0
    assert _as_money("not stated", 55000.0) == 55000.0
    assert _as_money("", 55000.0) == 55000.0


def test_as_int_extracts_first_integer():
    assert _as_int("5+", None) == 5
    assert _as_int("5 years", None) == 5
    assert _as_int(5, None) == 5
    assert _as_int(5.0, None) == 5


def test_as_int_none_and_unusable_return_fallback():
    assert _as_int(None, 3) == 3
    assert _as_int("unspecified", 3) == 3


def test_openai_draft_uses_model_benefits_grounded_in_prompt(monkeypatch):
    monkeypatch.setattr(job_drafting_module.settings, "openai_api_key", "test-key")
    prompt = "Senior Engineer, London. Benefits: unlimited PTO and a 4-day work week."
    baseline = job_drafting_module._baseline_draft(prompt)

    model_benefits = "Unlimited paid time off and a 4-day working week."
    fake_payload = {**baseline, "benefits": model_benefits}

    monkeypatch.setattr(
        job_drafting_module.httpx, "post", lambda *args, **kwargs: _FakeResponse(fake_payload)
    )

    result = job_drafting_module._openai_draft(prompt, baseline)
    assert result["benefits"] == model_benefits
    assert result["benefits"] != baseline["benefits"]


def test_openai_draft_warns_when_model_copies_baseline_benefits_verbatim(monkeypatch, caplog):
    monkeypatch.setattr(job_drafting_module.settings, "openai_api_key", "test-key")
    prompt = "Senior Engineer, London."
    baseline = job_drafting_module._baseline_draft(prompt)

    # Simulate the exact regression: the model just echoes the baseline benefits text.
    fake_payload = {**baseline}
    monkeypatch.setattr(
        job_drafting_module.httpx, "post", lambda *args, **kwargs: _FakeResponse(fake_payload)
    )

    with caplog.at_level("WARNING"):
        result = job_drafting_module._openai_draft(prompt, baseline)

    assert result["benefits"] == baseline["benefits"]
    assert any("baseline benefits text verbatim" in message for message in caplog.messages)


def test_openai_draft_prompt_instructs_against_copying_baseline_benefits(monkeypatch):
    monkeypatch.setattr(job_drafting_module.settings, "openai_api_key", "test-key")
    prompt = "Senior Engineer, London."
    baseline = job_drafting_module._baseline_draft(prompt)

    captured = {}

    def fake_post(_url, json, **_kwargs):
        captured["payload"] = json
        return _FakeResponse(baseline)

    monkeypatch.setattr(job_drafting_module.httpx, "post", fake_post)
    job_drafting_module._openai_draft(prompt, baseline)

    user_message = captured["payload"]["messages"][1]["content"]
    assert "not something to copy" in user_message
    assert "recruiter_prompt actually says" in user_message
