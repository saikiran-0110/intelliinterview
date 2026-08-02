from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="sched-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Sched Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_session(client, recruiter_token: str, candidate_email: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Sched Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    job_response = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Backend Engineer", "description": SAMPLE_JOB_SPEC},
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
    session_response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={"question_plan_id": plan_response.json()["id"], "candidate_email": candidate_email},
    )
    assert session_response.status_code == 201
    return session_response.json()["id"]


def test_propose_slots_notifies_and_candidate_can_confirm(client):
    recruiter_token = register_recruiter(client, email="sched-recruiter@example.com")
    candidate_email = "slot-candidate@example.com"
    candidate_token = _register_candidate(client, email=candidate_email)
    session_id = _create_session(client, recruiter_token, candidate_email)

    propose = client.post(
        "/api/scheduling/propose",
        headers=auth_headers(recruiter_token),
        json={"session_id": session_id, "slot_count": 3, "duration_minutes": 45},
    )
    assert propose.status_code == 201
    payload = propose.json()
    assert len(payload["slots"]) == 3
    assert payload["confirmation_status"] == "PENDING"

    notifications = client.get("/api/scheduling/notifications", headers=auth_headers(candidate_token))
    assert notifications.status_code == 200
    assert any("slots available" in item["title"].lower() for item in notifications.json())

    slot_id = payload["slots"][0]["id"]
    confirm = client.post(
        f"/api/scheduling/{session_id}/confirm",
        headers=auth_headers(candidate_token),
        json={"slot_id": slot_id, "candidate_note": "Works for me"},
    )
    assert confirm.status_code == 200
    assert confirm.json()["confirmation_status"] == "CONFIRMED"
    assert confirm.json()["scheduled_at"] is not None


def test_candidate_can_request_reschedule(client):
    recruiter_token = register_recruiter(client, email="resched-recruiter@example.com")
    candidate_email = "resched-candidate@example.com"
    candidate_token = _register_candidate(client, email=candidate_email)
    session_id = _create_session(client, recruiter_token, candidate_email)

    client.post(
        "/api/scheduling/propose",
        headers=auth_headers(recruiter_token),
        json={"session_id": session_id, "slot_count": 2},
    )
    response = client.post(
        f"/api/scheduling/{session_id}/reschedule",
        headers=auth_headers(candidate_token),
        json={"candidate_note": "Please suggest afternoon slots"},
    )
    assert response.status_code == 200
    assert response.json()["confirmation_status"] == "RESCHEDULE_REQUESTED"
