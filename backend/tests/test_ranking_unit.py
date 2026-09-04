from app.models import PipelineStage
from app.services.ranking import READY_TO_SHORTLIST, _plain_language, _skill_names


def test_skill_names_from_dicts_and_strings():
    assert _skill_names([{"name": "python"}, "fastapi", {"name": "  "}, ""]) == ["python", "fastapi"]


def test_plain_language_levels():
    strong = _plain_language(80, ["python", "fastapi"], ["kubernetes"])
    assert "strong overall match" in strong
    assert "score 80/100" in strong
    moderate = _plain_language(60, [], ["rust"])
    assert "moderate match" in moderate
    assert "limited confirmed skill overlap" in moderate
    weak = _plain_language(40, ["sql"], [])
    assert "weak match" in weak
    assert "no major skill gaps flagged" in weak


def test_ready_to_shortlist_stages():
    assert PipelineStage.APPLIED in READY_TO_SHORTLIST
    assert PipelineStage.SCREENING in READY_TO_SHORTLIST
    assert PipelineStage.HIRED not in READY_TO_SHORTLIST
