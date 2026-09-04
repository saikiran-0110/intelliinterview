from app.services.gap_analysis import (
    _build_evidence_passages,
    _build_experience_analysis,
    _build_narrative_summary,
    _build_qualifications_analysis,
    _calculate_match_score,
)


def test_experience_alignment_strong_partial_and_gap():
    strong = _build_experience_analysis(
        {"years_experience": 6, "seniority": "senior"},
        {"years_experience_required": 5, "seniority_required": "senior"},
    )
    assert strong["alignment"] == "strong"

    partial = _build_experience_analysis(
        {"years_experience": 4, "seniority": "mid"},
        {"years_experience_required": 5, "seniority_required": "senior"},
    )
    assert partial["alignment"] == "partial"

    gap = _build_experience_analysis(
        {"years_experience": 1, "seniority": "junior"},
        {"years_experience_required": 5, "seniority_required": "senior"},
    )
    assert gap["alignment"] == "gap"


def test_experience_unknown_when_years_missing():
    result = _build_experience_analysis({}, {"years_experience_required": 5})
    assert result["alignment"] == "unknown"
    assert "Role expects around 5+" in result["notes"][0]


def test_qualifications_alignment():
    strong = _build_qualifications_analysis(
        {"qualifications": ["Bachelor's degree"]},
        {"qualifications_required": ["Bachelor's degree"]},
    )
    assert strong["alignment"] == "strong"
    partial = _build_qualifications_analysis(
        {"qualifications": ["Bachelor's degree"]},
        {"qualifications_required": ["Bachelor's degree", "Master's degree"]},
    )
    assert partial["alignment"] == "partial"
    gap = _build_qualifications_analysis(
        {"qualifications": []},
        {"qualifications_required": ["Master's degree"]},
    )
    assert gap["alignment"] == "gap"
    unspecified = _build_qualifications_analysis({"qualifications": []}, {})
    assert unspecified["alignment"] == "not_specified"


def test_match_score_weights_and_experience_adjustment():
    assert _calculate_match_score(0, 0, 0, "unknown") == 50.0
    assert _calculate_match_score(2, 0, 0, "unknown") == 100.0
    assert _calculate_match_score(1, 0, 1, "unknown") == 50.0
    boosted = _calculate_match_score(1, 0, 1, "strong")
    reduced = _calculate_match_score(1, 0, 1, "gap")
    assert boosted == 55.0
    assert reduced == 40.0


def test_narrative_and_evidence_passages():
    matches = {
        "strong": [{"name": "python"}],
        "partial": [{"name": "kubernetes"}],
        "gaps": [{"name": "rust"}],
    }
    narrative = _build_narrative_summary(
        "Alex",
        "Backend Engineer",
        matches,
        {"notes": ["Candidate reports 6 years of experience."]},
        {"matched_qualifications": ["Bachelor's degree"]},
    )
    assert "Alex was compared against the Backend Engineer role" in narrative
    assert "python" in narrative
    assert "kubernetes" in narrative

    passages = _build_evidence_passages("Built Python APIs and Kubernetes jobs.", matches)
    skills = {item["skill"] for item in passages}
    assert "python" in skills
    assert "kubernetes" in skills
