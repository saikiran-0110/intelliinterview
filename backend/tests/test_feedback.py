from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="feedback-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Feedback Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _complete_session(client, recruiter_token: str, candidate_token: str, candidate_email: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Feedback Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    job_response = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Full Stack Engineer", "description": SAMPLE_JOB_SPEC},
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
    session_id = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_response.json()["id"],
            "candidate_email": candidate_email,
            "follow_up_limit": 0,
        },
    ).json()["id"]

    client.post(f"/api/sessions/{session_id}/start", headers=auth_headers(candidate_token))
    answer = (
        "I led FastAPI services with PostgreSQL, measured latency with Prometheus, "
        "and documented trade-offs with the engineering team."
    )
    for _ in range(40):
        response = client.post(
            f"/api/sessions/{session_id}/answer",
            headers=auth_headers(candidate_token),
            json={"answer": answer},
        )
        assert response.status_code == 200
        if response.json()["status"] == "COMPLETED":
            return session_id
    raise AssertionError("Session did not complete")


def test_candidate_receives_feedback_after_interview(client):
    recruiter_token = register_recruiter(client, email="feedback-recruiter@example.com")
    candidate_email = "feedback-live@example.com"
    candidate_token = _register_candidate(client, email=candidate_email)
    session_id = _complete_session(client, recruiter_token, candidate_token, candidate_email)

    listed = client.get("/api/feedback/me", headers=auth_headers(candidate_token))
    assert listed.status_code == 200
    assert any(item["session_id"] == session_id for item in listed.json())

    detail = client.get(f"/api/feedback/by-session/{session_id}", headers=auth_headers(candidate_token))
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["summary"]
    assert payload["strong_answers"] or payload["improvement_areas"]
    assert payload["focus_tips"]
