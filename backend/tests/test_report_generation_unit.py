from app.models import HiringRecommendation
from app.services.report_generation import (
    _build_summary,
    _mean,
    _recommendation_from_score,
    _recommendation_label,
    _unique_keep_order,
)


def test_mean_and_unique_keep_order():
    assert _mean([]) == 5.0
    assert _mean([8.0, 6.0]) == 7.0
    assert _unique_keep_order([" Python ", "python", "FastAPI", "", "Docker", "sql", "git", "aws", "react"]) == [
        "Python",
        "FastAPI",
        "Docker",
        "sql",
        "git",
        "aws",
        "react",
    ]


def test_recommendation_thresholds_and_summary():
    assert _recommendation_from_score(8.0) == HiringRecommendation.STRONG_HIRE
    assert _recommendation_from_score(6.5) == HiringRecommendation.HIRE
    assert _recommendation_from_score(5.0) == HiringRecommendation.HOLD
    assert _recommendation_from_score(4.9) == HiringRecommendation.NO_HIRE
    assert _recommendation_label(HiringRecommendation.STRONG_HIRE) == "Strong Hire"

    summary = _build_summary("Alex", "Backend Engineer", 8.2, HiringRecommendation.STRONG_HIRE, ["APIs"], [])
    assert "Alex scored 8.2/10" in summary
    assert "Strong Hire" in summary
    assert "no major weaknesses flagged" in summary
