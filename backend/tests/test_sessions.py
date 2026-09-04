from tests.helpers import auth_headers, confirm_session_for_interview, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Alex Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_plan(client, recruiter_token: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Alex Morgan"},
        files={"file": ("alex-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
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


def test_live_interview_flow_with_follow_up_and_evidence(client):
    recruiter_token = register_recruiter(client, email="session-recruiter@example.com")
    candidate_token = _register_candidate(client, email="live-candidate@example.com")
    plan_id = _create_plan(client, recruiter_token)

    create_response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": "live-candidate@example.com",
            "follow_up_limit": 1,
        },
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]
    assert create_response.json()["status"] == "SCHEDULED"
    confirm_session_for_interview(client, recruiter_token, session_id)

    start_response = client.post(
        f"/api/sessions/{session_id}/start",
        headers=auth_headers(candidate_token),
    )
    assert start_response.status_code == 200
    started = start_response.json()
    assert started["status"] == "IN_PROGRESS"
    assert started["turns"][0]["role"] == "INTERVIEWER"
    assert started["progress"]["total"] >= 1

    short_answer = client.post(
        f"/api/sessions/{session_id}/answer",
        headers=auth_headers(candidate_token),
        json={"answer": "Yes."},
    )
    assert short_answer.status_code == 200
    after_short = short_answer.json()
    assert any(turn["role"] == "CANDIDATE" for turn in after_short["turns"])
    candidate_turns = [turn for turn in after_short["turns"] if turn["role"] == "CANDIDATE"]
    assert candidate_turns[0]["evaluation"] is not None
    assert candidate_turns[0]["evaluation"]["evidence_quotes"]

    # Short answer should trigger a follow-up when limit allows.
    assert after_short["turns"][-1]["role"] == "INTERVIEWER"
    assert after_short["turns"][-1]["is_follow_up"] is True

    follow_up_answer = client.post(
        f"/api/sessions/{session_id}/answer",
        headers=auth_headers(candidate_token),
        json={
            "answer": (
                "In my last role I led API design with FastAPI and PostgreSQL, measured latency "
                "improvements, and documented trade-offs for the team."
            )
        },
    )
    assert follow_up_answer.status_code == 200
    after_follow_up = follow_up_answer.json()
    assert after_follow_up["status"] in {"IN_PROGRESS", "COMPLETED"}
    assert after_follow_up["turns"][-1]["role"] == "INTERVIEWER"

    recruiter_view = client.get(
        f"/api/sessions/{session_id}",
        headers=auth_headers(recruiter_token),
    )
    assert recruiter_view.status_code == 200
    assert len(recruiter_view.json()["turns"]) >= 3


def test_candidate_cannot_start_other_session(client):
    recruiter_token = register_recruiter(client, email="owner-recruiter@example.com")
    _register_candidate(client, email="assigned@example.com")
    other_token = _register_candidate(client, email="other@example.com")
    plan_id = _create_plan(client, recruiter_token)

    session_id = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={"question_plan_id": plan_id, "candidate_email": "assigned@example.com"},
    ).json()["id"]

    response = client.post(
        f"/api/sessions/{session_id}/start",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404
