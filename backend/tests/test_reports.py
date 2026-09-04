from tests.helpers import auth_headers, confirm_session_for_interview, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="report-candidate@example.com"):
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


def _complete_session(client, recruiter_token: str, candidate_token: str, candidate_email: str) -> str:
    plan_id = _create_plan(client, recruiter_token)
    session_id = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": candidate_email,
            "follow_up_limit": 0,
        },
    ).json()["id"]
    confirm_session_for_interview(client, recruiter_token, session_id)

    start = client.post(
        f"/api/sessions/{session_id}/start",
        headers=auth_headers(candidate_token),
    )
    assert start.status_code == 200

    detailed_answer = (
        "In my last role I led API design with FastAPI and PostgreSQL, measured latency "
        "improvements with Prometheus, and documented trade-offs for the engineering team."
    )

    for _ in range(40):
        response = client.post(
            f"/api/sessions/{session_id}/answer",
            headers=auth_headers(candidate_token),
            json={"answer": detailed_answer},
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "COMPLETED":
            return session_id

    raise AssertionError("Session did not complete after answering all questions")


def test_report_generated_when_session_completes(client):
    recruiter_token = register_recruiter(client, email="report-recruiter@example.com")
    candidate_email = "report-live@example.com"
    candidate_token = _register_candidate(client, email=candidate_email)

    session_id = _complete_session(client, recruiter_token, candidate_token, candidate_email)

    by_session = client.get(
        f"/api/reports/by-session/{session_id}",
        headers=auth_headers(recruiter_token),
    )
    assert by_session.status_code == 200
    report = by_session.json()
    assert report["session_id"] == session_id
    assert report["overall_score"] >= 0
    assert report["technical_fit_score"] >= 0
    assert report["communication_score"] >= 0
    assert report["problem_solving_score"] >= 0
    assert report["role_alignment_score"] >= 0
    assert report["recommendation"] in {"STRONG_HIRE", "HIRE", "HOLD", "NO_HIRE"}
    assert report["recommendation_summary"]
    assert isinstance(report["strengths"], list)
    assert isinstance(report["weaknesses"], list)
    assert isinstance(report["evidence_items"], list)
    assert len(report["evidence_items"]) >= 1

    listed = client.get("/api/reports", headers=auth_headers(recruiter_token))
    assert listed.status_code == 200
    assert any(item["id"] == report["id"] for item in listed.json())

    detail = client.get(f"/api/reports/{report['id']}", headers=auth_headers(recruiter_token))
    assert detail.status_code == 200
    assert detail.json()["id"] == report["id"]


def test_generate_report_rejects_incomplete_session(client):
    recruiter_token = register_recruiter(client, email="incomplete-report@example.com")
    candidate_token = _register_candidate(client, email="incomplete-candidate@example.com")
    plan_id = _create_plan(client, recruiter_token)

    session_id = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_id,
            "candidate_email": "incomplete-candidate@example.com",
            "follow_up_limit": 0,
        },
    ).json()["id"]

    client.post(f"/api/sessions/{session_id}/start", headers=auth_headers(candidate_token))

    response = client.post(
        f"/api/reports/generate/{session_id}",
        headers=auth_headers(recruiter_token),
    )
    assert response.status_code == 400
