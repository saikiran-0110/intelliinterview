from tests.helpers import auth_headers, register_candidate, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _open_job_and_cv(client, recruiter_token: str, candidate_token: str) -> tuple[str, str]:
    job = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    )
    assert job.status_code == 201
    cv = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate_token),
        data={"candidate_name": "Prep Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert cv.status_code == 201
    return job.json()["id"], cv.json()["id"]


def test_preparation_generate_progress_and_delete(client):
    recruiter = register_recruiter(client, email="prep-recruiter@example.com")
    candidate = register_candidate(client, email="prep-candidate@example.com", full_name="Prep Candidate")
    job_id, cv_id = _open_job_and_cv(client, recruiter, candidate)

    generated = client.post(
        "/api/preparation/generate",
        headers=auth_headers(candidate),
        json={"job_spec_id": job_id, "cv_id": cv_id},
    )
    assert generated.status_code == 201
    pack = generated.json()
    assert pack["job_title"] == "Platform Engineer"
    assert pack["practice_questions"]
    pack_id = pack["id"]
    first_item = pack["practice_questions"][0]["id"]

    listed = client.get("/api/preparation/me", headers=auth_headers(candidate))
    assert listed.status_code == 200
    assert any(item["id"] == pack_id for item in listed.json())

    progressed = client.patch(
        f"/api/preparation/{pack_id}/progress",
        headers=auth_headers(candidate),
        json={"item_id": first_item, "completed": True},
    )
    assert progressed.status_code == 200
    assert first_item in progressed.json()["completed_item_ids"]
    assert progressed.json()["progress_percent"] >= 0

    deleted = client.delete(f"/api/preparation/{pack_id}", headers=auth_headers(candidate))
    assert deleted.status_code == 204


def test_preparation_requires_existing_job(client):
    candidate = register_candidate(client, email="prep-missing@example.com")
    response = client.post(
        "/api/preparation/generate",
        headers=auth_headers(candidate),
        json={"job_spec_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 404


def test_assistant_query_returns_tools(client):
    recruiter = register_recruiter(client, email="assistant-recruiter@example.com")
    client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC},
    )
    response = client.post(
        "/api/assistant/query",
        headers=auth_headers(recruiter),
        json={"message": "Who is the top candidate to shortlist?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert "find_best_candidates" in payload["tools_used"]


def test_assistant_requires_recruiter(client):
    candidate = register_candidate(client, email="assistant-blocked@example.com")
    response = client.post(
        "/api/assistant/query",
        headers=auth_headers(candidate),
        json={"message": "summarise pipeline"},
    )
    assert response.status_code == 403


def test_bias_acknowledge_flow(client):
    recruiter = register_recruiter(client, email="bias-ack@example.com")
    overview = client.get("/api/bias/overview", headers=auth_headers(recruiter))
    assert overview.status_code == 200
    alert_id = overview.json()["alerts"][0]["id"]

    ack = client.post(
        f"/api/bias/alerts/{alert_id}/acknowledge",
        headers=auth_headers(recruiter),
    )
    assert ack.status_code == 200
    assert ack.json()["acknowledged"] is True

    missing = client.post(
        "/api/bias/alerts/00000000-0000-0000-0000-000000000001/acknowledge",
        headers=auth_headers(recruiter),
    )
    assert missing.status_code == 404


def test_list_my_applications_after_apply(client):
    recruiter = register_recruiter(client, email="apps-recruiter@example.com")
    candidate = register_candidate(client, email="apps-candidate@example.com", full_name="Apps Candidate")
    job_id, cv_id = _open_job_and_cv(client, recruiter, candidate)
    applied = client.post(
        "/api/applications",
        headers=auth_headers(candidate),
        json={
            "job_spec_id": job_id,
            "cv_id": cv_id,
            "contact_full_name": "Apps Candidate",
            "contact_email": "apps-candidate@example.com",
            "contact_phone": "+44 7700 900444",
            "current_location": "London, UK",
            "right_to_work_uk": True,
        },
    )
    assert applied.status_code == 201
    mine = client.get("/api/applications/me", headers=auth_headers(candidate))
    assert mine.status_code == 200
    assert any(item["job_spec_id"] == job_id for item in mine.json())

    recruiter_list = client.get("/api/applications", headers=auth_headers(recruiter))
    assert recruiter_list.status_code == 200
    application_id = applied.json()["id"]
    staged = client.patch(
        f"/api/applications/{application_id}/stage",
        headers=auth_headers(recruiter),
        json={"stage": "SCREENING", "notes": "Reviewing"},
    )
    assert staged.status_code == 200
    assert staged.json()["stage"] == "SCREENING"
