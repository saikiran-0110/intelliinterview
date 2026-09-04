from types import SimpleNamespace

from app.services.candidate_feedback import _baseline_feedback
from app.services.preparation import _normalize_questions, _slug
from app.services.question_generation import _skill_name


def test_slug_and_question_normalization():
    assert _slug("System Design!!") == "system-design"
    questions = _normalize_questions(
        [
            {"question": "Explain FastAPI?", "difficulty": "easy", "talking_points": ["routing", ""]},
            "Describe Kubernetes scaling.",
            {"text": "   "},
            "",
        ]
    )
    assert len(questions) == 2
    assert questions[0]["question"] == "Explain FastAPI?"
    assert questions[0]["talking_points"] == ["routing"]
    assert questions[1]["question"] == "Describe Kubernetes scaling."
    assert questions[1]["difficulty"] == "intermediate"


def test_skill_name_from_string_or_dict():
    assert _skill_name("python") == "python"
    assert _skill_name({"name": " kubernetes "}) == "kubernetes"


def test_baseline_feedback_fills_defaults():
    report = SimpleNamespace(strengths=[], weaknesses=[])
    payload = _baseline_feedback(report, "Platform Engineer")
    assert "Platform Engineer" in payload["summary"]
    assert payload["strong_answers"]
    assert payload["improvement_areas"]
    assert len(payload["focus_tips"]) == 3
