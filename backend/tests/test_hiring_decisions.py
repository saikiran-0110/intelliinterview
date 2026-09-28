from tests.helpers import auth_headers, register_candidate, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _apply_for_job(client, recruiter_token: str, candidate_token: str, email: str) -> tuple[str, str]:
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
        data={"candidate_name": "Decision Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert cv.status_code == 201

    applied = client.post(
        "/api/applications",
        headers=auth_headers(candidate_token),
        json={
            "job_spec_id": job_id,
            "cv_id": cv.json()["id"],
            "contact_full_name": "Decision Candidate",
            "contact_email": email,
            "contact_phone": "+44 7700 900555",
            "right_to_work_uk": True,
        },
    )
    assert applied.status_code == 201
    return applied.json()["id"], job_id


def test_reject_decision_sends_polite_email(client):
    recruiter = register_recruiter(client, email="reject-recruiter@example.com")
    candidate = register_candidate(client, email="reject-candidate@example.com", full_name="Decision Candidate")
    application_id, _ = _apply_for_job(client, recruiter, candidate, "reject-candidate@example.com")

    staged = client.patch(
        f"/api/applications/{application_id}/stage",
        headers=auth_headers(recruiter),
        json={"stage": "REJECTED"},
    )
    assert staged.status_code == 200

    inbox = client.get("/api/scheduling/notifications", headers=auth_headers(candidate))
    assert any("not be moving forward" in n["body"] for n in inbox.json())


def test_advance_to_next_stage_sends_selection_email(client):
    recruiter = register_recruiter(client, email="advance-recruiter@example.com")
    candidate = register_candidate(client, email="advance-candidate@example.com", full_name="Decision Candidate")
    application_id, _ = _apply_for_job(client, recruiter, candidate, "advance-candidate@example.com")

    staged = client.patch(
        f"/api/applications/{application_id}/stage",
        headers=auth_headers(recruiter),
        json={"stage": "OFFER", "notes": "Please prepare for a technical round with the CTO."},
    )
    assert staged.status_code == 200

    inbox = client.get("/api/scheduling/notifications", headers=auth_headers(candidate))
    decision = next(n for n in inbox.json() if "passed the screening interview" in n["body"])
    assert "technical round with the CTO" in decision["body"]


def test_report_exposes_application_id_and_stage_for_hiring_decisions(client):
    from tests.test_reports import _complete_session, _register_candidate

    recruiter = register_recruiter(client, email="report-decision-recruiter@example.com")
    candidate_email = "report-decision-candidate@example.com"
    candidate = _register_candidate(client, email=candidate_email)

    session_id = _complete_session(client, recruiter, candidate, candidate_email)
    report = client.get(
        f"/api/reports/by-session/{session_id}",
        headers=auth_headers(recruiter),
    ).json()

    # No JobApplication exists for this direct-session flow, so the hiring
    # decision panel simply has nothing to act on yet.
    assert report["application_id"] is None
    assert report["application_stage"] is None
    assert report["candidate_has_photo"] is False
