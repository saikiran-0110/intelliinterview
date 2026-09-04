from types import SimpleNamespace

from app.services.interview_agent import _baseline_evaluate, _word_count


def test_word_count_ignores_extra_whitespace():
    assert _word_count("  one   two three  ") == 3
    assert _word_count("") == 0


def test_short_answer_requests_follow_up():
    question = SimpleNamespace(skill_ref="python", topic="python")
    result = _baseline_evaluate("Yes.", question, follow_up_count=0, follow_up_limit=1)
    assert result["should_follow_up"] is True
    assert result["advance_question"] is False
    assert result["technical_score"] == 3.0
    assert result["follow_up_question"]
    assert result["evidence_quotes"]


def test_detailed_answer_mentions_skill_and_advances():
    question = SimpleNamespace(skill_ref="FastAPI", topic="backend")
    answer = (
        "FastAPI production work: "
        + "latency metrics retries dashboards runbooks incidents mentoring "
        * 10
    )
    result = _baseline_evaluate(answer, question, follow_up_count=0, follow_up_limit=1)
    assert result["should_follow_up"] is False
    assert result["advance_question"] is True
    assert result["technical_score"] == 7.5
    assert any("FastAPI" in item for item in result["strengths"])
