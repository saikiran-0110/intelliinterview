from tests.helpers import auth_headers, register_candidate, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def test_list_get_and_download_cv(client):
    token = register_candidate(client, email="cv-owner@example.com", full_name="CV Owner")
    upload = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        data={"candidate_name": "CV Owner"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 201
    cv_id = upload.json()["id"]

    listed = client.get("/api/cvs", headers=auth_headers(token))
    assert listed.status_code == 200
    assert any(item["id"] == cv_id for item in listed.json())

    detail = client.get(f"/api/cvs/{cv_id}", headers=auth_headers(token))
    assert detail.status_code == 200
    assert detail.json()["candidate_name"] == "CV Owner"

    download = client.get(f"/api/cvs/{cv_id}/download", headers=auth_headers(token))
    assert download.status_code == 200
    assert b"Alex Morgan" in download.content or b"Python" in download.content

    other = register_candidate(client, email="other-cv@example.com")
    blocked = client.get(f"/api/cvs/{cv_id}", headers=auth_headers(other))
    assert blocked.status_code == 404


def test_candidate_can_delete_own_cv(client):
    token = register_candidate(client, email="cv-delete@example.com")
    cv_id = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    ).json()["id"]

    deleted = client.delete(f"/api/cvs/{cv_id}", headers=auth_headers(token))
    assert deleted.status_code == 204
    missing = client.get(f"/api/cvs/{cv_id}", headers=auth_headers(token))
    assert missing.status_code == 404


def test_upload_rejects_unsupported_file(client):
    token = register_recruiter(client, email="cv-badfile@example.com")
    response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        data={"candidate_name": "Alex"},
        files={"file": ("notes.xlsx", b"not-a-cv", "application/vnd.ms-excel")},
    )
    assert response.status_code == 400


def test_list_job_specs_and_toggle_visibility(client):
    recruiter = register_recruiter(client, email="jobs-owner@example.com")
    created = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter),
        json={"title": "Backend Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    )
    assert created.status_code == 201
    job_id = created.json()["id"]

    listed = client.get("/api/job-specs", headers=auth_headers(recruiter))
    assert listed.status_code == 200
    assert any(item["id"] == job_id for item in listed.json())

    closed = client.patch(
        f"/api/job-specs/{job_id}/visibility",
        headers=auth_headers(recruiter),
        json={"is_open": False},
    )
    assert closed.status_code == 200
    assert closed.json()["is_open"] is False

    candidate = register_candidate(client, email="jobs-viewer@example.com")
    open_jobs = client.get("/api/job-specs/open", headers=auth_headers(candidate))
    assert open_jobs.status_code == 200
    assert all(item["id"] != job_id for item in open_jobs.json())


def test_candidate_cannot_create_job_spec(client):
    token = register_candidate(client, email="not-recruiter@example.com")
    response = client.post(
        "/api/job-specs",
        headers=auth_headers(token),
        json={"title": "Nope", "description": SAMPLE_JOB_SPEC},
    )
    assert response.status_code == 403


def test_ranking_missing_job_returns_404(client):
    token = register_recruiter(client, email="rank-missing@example.com")
    response = client.get(
        "/api/ranking/00000000-0000-0000-0000-000000000001",
        headers=auth_headers(token),
    )
    assert response.status_code == 404
