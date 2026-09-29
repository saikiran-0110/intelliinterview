from tests.helpers import auth_headers, register_candidate, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _apply_for_job(client, recruiter_token: str, candidate_email: str, candidate_token: str) -> None:
    job = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    )
    cv = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate_token),
        data={"candidate_name": "Notif Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    applied = client.post(
        "/api/applications",
        headers=auth_headers(candidate_token),
        json={
            "job_spec_id": job.json()["id"],
            "cv_id": cv.json()["id"],
            "contact_full_name": "Notif Candidate",
            "contact_email": candidate_email,
            "contact_phone": "+44 7700 900777",
            "right_to_work_uk": True,
        },
    )
    assert applied.status_code == 201


def test_mark_all_notifications_read(client):
    recruiter = register_recruiter(client, email="notif-recruiter@example.com")
    for i in range(3):
        candidate_email = f"notif-candidate-{i}@example.com"
        candidate = register_candidate(client, email=candidate_email, full_name=f"Notif Candidate {i}")
        _apply_for_job(client, recruiter, candidate_email, candidate)

    before = client.get("/api/scheduling/notifications", headers=auth_headers(recruiter)).json()
    assert sum(1 for item in before if not item["is_read"]) >= 3

    marked = client.post("/api/scheduling/notifications/read-all", headers=auth_headers(recruiter))
    assert marked.status_code == 200
    assert all(item["is_read"] for item in marked.json())

    after = client.get("/api/scheduling/notifications", headers=auth_headers(recruiter)).json()
    assert all(item["is_read"] for item in after)


def test_mark_all_notifications_read_only_affects_current_user(client):
    recruiter_a = register_recruiter(client, email="notif-scope-a@example.com")
    recruiter_b = register_recruiter(client, email="notif-scope-b@example.com")
    candidate_email = "notif-scope-candidate@example.com"
    candidate = register_candidate(client, email=candidate_email, full_name="Scope Candidate")
    _apply_for_job(client, recruiter_a, candidate_email, candidate)

    client.post("/api/scheduling/notifications/read-all", headers=auth_headers(recruiter_b))

    recruiter_a_notifications = client.get(
        "/api/scheduling/notifications", headers=auth_headers(recruiter_a)
    ).json()
    assert any(not item["is_read"] for item in recruiter_a_notifications)
