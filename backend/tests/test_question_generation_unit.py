from types import SimpleNamespace

from app.services.question_generation import _build_baseline_questions, _skill_name


def test_skill_name_handles_missing_name():
    assert _skill_name({}) == ""


def test_baseline_questions_cover_gaps_and_partials():
    analysis = SimpleNamespace(
        gaps=[{"name": "kubernetes"}],
        partial_matches=[{"name": "aws", "related_cv_skill": "docker"}],
        strong_matches=[{"name": "python"}],
        experience_analysis={"alignment": "partial", "notes": ["Slightly below required years."]},
        qualifications_analysis={"missing_qualifications": ["Master's degree"]},
        evidence_passages=[],
    )
    questions = _build_baseline_questions("Alex", "Platform Engineer", analysis)
    topics = {item["topic"] for item in questions}
    texts = " ".join(item["text"] for item in questions)
    assert "kubernetes" in topics
    assert "aws" in topics
    assert "python" in topics
    assert "Platform Engineer" in texts
    assert len(questions) >= 3
