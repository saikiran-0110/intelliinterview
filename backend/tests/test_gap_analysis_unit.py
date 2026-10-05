import copy
import json
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.services.gap_analysis as gap_analysis_module
from app.database import Base
from app.models import CandidateCv, JobSpecification, User, UserRole
from app.services.embeddings import clear_skill_phrase_cache
from app.services.gap_analysis import (
    GapAnalysisService,
    _apply_semantic_layer,
    _build_evidence_passages,
    _build_experience_analysis,
    _build_narrative_summary,
    _build_qualifications_analysis,
    _calculate_match_score,
    _ensure_embedded_chunks,
)
from app.services.skill_catalog import compare_skills


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


CV_CHUNKS = [
    {
        "text": "Led the migration of our platform to Kubernetes clusters across every production service.",
        "vector": [1.0, 0.0, 0.0],
    },
    {
        "text": "Built REST APIs in Python using Flask for the customer-facing web application.",
        "vector": [0.0, 1.0, 0.0],
    },
]


def _fake_embed_texts_factory(monkeypatch):
    """Route kubernetes' skill-phrase embedding onto the first CV chunk's vector
    (similarity 1.0) and every other skill phrase onto an orthogonal vector
    (similarity 0.0 against every stored chunk) - deterministic and offline."""
    import app.services.embeddings as embeddings_module

    def fake_embed_texts(texts):
        phrase = texts[0].lower()
        if "kubernetes" in phrase:
            return [[1.0, 0.0, 0.0]]
        return [[0.0, 0.0, 1.0]]

    monkeypatch.setattr(embeddings_module, "embed_texts", fake_embed_texts)


def test_semantic_rescue_promotes_gap_above_threshold(monkeypatch):
    clear_skill_phrase_cache()
    _fake_embed_texts_factory(monkeypatch)

    matches = compare_skills(cv_skills=[], job_skills=["kubernetes", "security"])
    assert {item["name"] for item in matches["gaps"]} == {"kubernetes", "security"}

    cv = SimpleNamespace(embedded_chunks=CV_CHUNKS)
    passages = _apply_semantic_layer(cv, matches)

    gap_names = {item["name"] for item in matches["gaps"]}
    partial_names = {item["name"] for item in matches["partial"]}

    assert "kubernetes" not in gap_names
    assert "kubernetes" in partial_names
    promoted = next(item for item in matches["partial"] if item["name"] == "kubernetes")
    assert promoted["match_source"] == "semantic"
    assert promoted["similarity"] == 1.0
    assert "Semantically matched" in promoted["rationale"]

    clear_skill_phrase_cache()


def test_semantic_rescue_leaves_below_threshold_skill_in_gaps(monkeypatch):
    clear_skill_phrase_cache()
    _fake_embed_texts_factory(monkeypatch)

    matches = compare_skills(cv_skills=[], job_skills=["security"])
    cv = SimpleNamespace(embedded_chunks=CV_CHUNKS)
    _apply_semantic_layer(cv, matches)

    assert matches["partial"] == []
    assert len(matches["gaps"]) == 1
    assert matches["gaps"][0]["name"] == "security"
    assert matches["gaps"][0]["match_source"] == "catalogue"

    clear_skill_phrase_cache()


def test_semantic_rescue_is_a_noop_without_embedded_chunks(monkeypatch):
    clear_skill_phrase_cache()
    _fake_embed_texts_factory(monkeypatch)

    baseline_matches = compare_skills(
        cv_skills=["python"], job_skills=["python", "kubernetes", "security"]
    )
    rescued_matches = copy.deepcopy(baseline_matches)

    cv_no_chunks = SimpleNamespace(embedded_chunks=None)
    passages = _apply_semantic_layer(cv_no_chunks, rescued_matches)

    # Classification (which skills land in which bucket) is unchanged from the pure
    # lexical result - only the provenance tag is added universally.
    assert {item["name"] for item in rescued_matches["strong"]} == {
        item["name"] for item in baseline_matches["strong"]
    }
    assert {item["name"] for item in rescued_matches["partial"]} == {
        item["name"] for item in baseline_matches["partial"]
    }
    assert {item["name"] for item in rescued_matches["gaps"]} == {
        item["name"] for item in baseline_matches["gaps"]
    }
    assert passages == []

    clear_skill_phrase_cache()


def test_ensure_embedded_chunks_skips_when_no_api_key():
    from app.config import settings

    assert settings.openai_api_key == ""  # set globally for tests in conftest.py
    cv = SimpleNamespace(embedded_chunks=None, extracted_text="Some CV text about Python and Docker.")
    _ensure_embedded_chunks(cv)
    assert cv.embedded_chunks is None


def test_ensure_embedded_chunks_skips_when_already_populated(monkeypatch):
    import app.services.embeddings as embeddings_module
    from app.config import settings

    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(embeddings_module, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key")

    cv = SimpleNamespace(embedded_chunks=[{"text": "existing", "vector": [1.0, 0.0]}], extracted_text="irrelevant")
    _ensure_embedded_chunks(cv)

    assert calls == []
    assert cv.embedded_chunks == [{"text": "existing", "vector": [1.0, 0.0]}]


class _FakeChatResponse:
    def __init__(self, content: dict):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": json.dumps(self._content)}}]}


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_semantic_provenance_survives_openai_enhancement(monkeypatch, db_session):
    """Regression test for a real bug found via D6 live re-scoring: the OpenAI
    enhancement step replaces strong/partial/gaps with the model's own {name,
    rationale} dicts, which never carry match_source - so a semantically-promoted
    skill's provenance must be re-attached by name after enhancement, not depend on
    the model echoing a field it was never asked for."""
    clear_skill_phrase_cache()
    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key")

    import app.services.embeddings as embeddings_module

    def fake_embed_texts(texts):
        phrase = texts[0].lower()
        if "kubernetes" in phrase:
            return [[1.0, 0.0, 0.0]]
        return [[0.0, 0.0, 1.0]]

    monkeypatch.setattr(embeddings_module, "embed_texts", fake_embed_texts)

    # The model returns kubernetes as a partial match, as plain {name, rationale} -
    # no match_source, exactly like the real OpenAI response observed in practice.
    fake_chat_payload = {
        "strong_matches": [],
        "partial_matches": [{"name": "kubernetes", "rationale": "Related container experience."}],
        "gaps": [],
        "experience_analysis": {"alignment": "unknown", "notes": []},
        "qualifications_analysis": {"alignment": "not_specified"},
        "narrative_summary": "AI-rewritten narrative.",
    }
    monkeypatch.setattr(
        gap_analysis_module.httpx, "post", lambda *args, **kwargs: _FakeChatResponse(fake_chat_payload)
    )

    recruiter = User(
        id=uuid.uuid4(),
        email="semantic-test@example.com",
        password_hash="x",
        full_name="Recruiter",
        role=UserRole.RECRUITER,
    )
    cv = CandidateCv(
        id=uuid.uuid4(),
        candidate_name="Alex Morgan",
        original_filename="cv.txt",
        extracted_text="Led the migration of our platform to Kubernetes clusters across every service.",
        parsed_profile={"skills": [], "years_experience": None, "seniority": None, "qualifications": []},
        embedded_chunks=[
            {
                "text": "Led the migration of our platform to Kubernetes clusters across every service.",
                "vector": [1.0, 0.0, 0.0],
            }
        ],
        uploaded_by=recruiter.id,
    )
    job_spec = JobSpecification(
        id=uuid.uuid4(),
        title="Platform Engineer",
        description="Kubernetes required.",
        extracted_text="Kubernetes required.",
        parsed_requirements={
            "required_skills": ["kubernetes"],
            "years_experience_required": None,
            "seniority_required": None,
            "qualifications_required": [],
        },
        created_by=recruiter.id,
    )
    db_session.add_all([recruiter, cv, job_spec])
    db_session.commit()

    analysis = GapAnalysisService().analyse(db_session, cv, job_spec, recruiter.id)

    promoted = next(item for item in analysis.partial_matches if item["name"] == "kubernetes")
    assert promoted["match_source"] == "semantic"
    assert promoted["similarity"] == 1.0
    # The AI's own rationale is preserved too - only provenance is backfilled.
    assert promoted["rationale"] == "Related container experience."

    clear_skill_phrase_cache()
