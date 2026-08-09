from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="opt-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Optional Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def test_candidate_apply_rank_prepare_and_assistant(client):
    recruiter_token = register_recruiter(client, email="opt-recruiter@example.com")
    candidate_token = _register_candidate(client, email="opt-live@example.com")

    job = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    )
    assert job.status_code == 201
    job_id = job.json()["id"]

    cv = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate_token),
        data={"candidate_name": "Optional Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert cv.status_code == 201
    cv_id = cv.json()["id"]

    apply = client.post(
        "/api/applications",
        headers=auth_headers(candidate_token),
        json={"job_spec_id": job_id, "cv_id": cv_id},
    )
    assert apply.status_code == 201
    assert apply.json()["stage"] == "APPLIED"
    assert apply.json()["match_score"] is not None

    my_apps = client.get("/api/applications/me", headers=auth_headers(candidate_token))
    assert my_apps.status_code == 200
    assert len(my_apps.json()) >= 1

    ranking = client.get(f"/api/ranking/{job_id}", headers=auth_headers(recruiter_token))
    assert ranking.status_code == 200
    assert ranking.json()["candidates"]
    assert ranking.json()["candidates"][0]["plain_language_breakdown"]

    prep = client.post(
        "/api/preparation/generate",
        headers=auth_headers(candidate_token),
        json={"job_spec_id": job_id, "cv_id": cv_id},
    )
    assert prep.status_code == 201
    assert prep.json()["practice_questions"]
    assert prep.json()["guidance"]

    assistant = client.post(
        "/api/assistant/query",
        headers=auth_headers(recruiter_token),
        json={"message": "Who are the best candidates for Platform Engineer?"},
    )
    assert assistant.status_code == 200
    assert assistant.json()["answer"]
    assert assistant.json()["tools_used"]

    stage = client.patch(
        f"/api/applications/{apply.json()['id']}/stage",
        headers=auth_headers(recruiter_token),
        json={"stage": "SHORTLISTED"},
    )
    assert stage.status_code == 200
    assert stage.json()["stage"] == "SHORTLISTED"

    download = client.get(f"/api/cvs/{cv_id}/download", headers=auth_headers(recruiter_token))
    assert download.status_code == 200
    assert download.content
