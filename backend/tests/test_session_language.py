from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="lang-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Lang Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_plan(client, recruiter_token: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Lang Candidate"},
        files={"file": ("lang-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    job_response = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Senior Full Stack Engineer", "description": SAMPLE_JOB_SPEC},
    )
    analysis_response = client.post(
        "/api/analysis/gap",
        headers=auth_headers(recruiter_token),
        json={"cv_id": cv_response.json()["id"], "job_spec_id": job_response.json()["id"]},
    )
    plan_response = client.post(
        "/api/questions/generate",
        headers=auth_headers(recruiter_token),
        json={"gap_analysis_id": analysis_response.json()["id"]},
    )
    assert plan_response.status_code == 201
    return plan_response.json()["id"]


def test_session_creation_stores_and_returns_language(client):
    recruiter_token = register_recruiter(client, email="lang-recruiter@example.com")
    _register_candidate(client, email="lang-candidate@example.com")
    plan_id = _create_plan(client, recruiter_token)

    response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": "lang-candidate@example.com",
            "follow_up_limit": 1,
            "language": "fr-FR",
        },
    )
    assert response.status_code == 201
    assert response.json()["language"] == "fr-FR"

    session_id = response.json()["id"]
    fetched = client.get(f"/api/sessions/{session_id}", headers=auth_headers(recruiter_token))
    assert fetched.status_code == 200
    assert fetched.json()["language"] == "fr-FR"

    summary = client.get("/api/sessions", headers=auth_headers(recruiter_token))
    assert summary.status_code == 200
    assert any(item["id"] == session_id and item["language"] == "fr-FR" for item in summary.json())


def test_session_creation_falls_back_to_en_gb_for_invalid_language(client):
    recruiter_token = register_recruiter(client, email="lang-recruiter2@example.com")
    _register_candidate(client, email="lang-candidate2@example.com")
    plan_id = _create_plan(client, recruiter_token)

    response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": "lang-candidate2@example.com",
            "follow_up_limit": 1,
            "language": "klingon",
        },
    )
    assert response.status_code == 201
    assert response.json()["language"] == "en-GB"


def test_session_creation_defaults_to_en_gb_when_absent(client):
    recruiter_token = register_recruiter(client, email="lang-recruiter3@example.com")
    _register_candidate(client, email="lang-candidate3@example.com")
    plan_id = _create_plan(client, recruiter_token)

    response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": "lang-candidate3@example.com",
            "follow_up_limit": 1,
        },
    )
    assert response.status_code == 201
    assert response.json()["language"] == "en-GB"
