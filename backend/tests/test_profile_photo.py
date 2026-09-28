from tests.helpers import auth_headers, register_candidate, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC

FAKE_PNG = b"\x89PNG\r\n\x1a\nfake-image-bytes-for-tests"


def _me_id(client, token: str) -> str:
    return client.get("/api/auth/me", headers=auth_headers(token)).json()["user_id"]


def test_upload_view_and_delete_own_photo(client):
    candidate = register_candidate(client, email="photo-candidate@example.com")

    upload = client.post(
        "/api/auth/me/photo",
        headers=auth_headers(candidate),
        files={"file": ("me.png", FAKE_PNG, "image/png")},
    )
    assert upload.status_code == 200
    assert upload.json()["has_profile_photo"] is True

    candidate_id = _me_id(client, candidate)
    fetched = client.get(f"/api/auth/users/{candidate_id}/photo", headers=auth_headers(candidate))
    assert fetched.status_code == 200
    assert fetched.content == FAKE_PNG
    assert fetched.headers["content-type"].startswith("image/")

    deleted = client.delete("/api/auth/me/photo", headers=auth_headers(candidate))
    assert deleted.status_code == 200
    assert deleted.json()["has_profile_photo"] is False

    missing = client.get(f"/api/auth/users/{candidate_id}/photo", headers=auth_headers(candidate))
    assert missing.status_code == 404


def test_upload_rejects_non_image_files(client):
    candidate = register_candidate(client, email="photo-badtype@example.com")
    response = client.post(
        "/api/auth/me/photo",
        headers=auth_headers(candidate),
        files={"file": ("me.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_unrelated_recruiter_cannot_view_candidate_photo(client):
    candidate = register_candidate(client, email="photo-private@example.com")
    client.post(
        "/api/auth/me/photo",
        headers=auth_headers(candidate),
        files={"file": ("me.png", FAKE_PNG, "image/png")},
    )
    candidate_id = _me_id(client, candidate)

    outsider = register_recruiter(client, email="photo-outsider@example.com")
    response = client.get(f"/api/auth/users/{candidate_id}/photo", headers=auth_headers(outsider))
    assert response.status_code == 404


def test_recruiter_linked_via_application_can_view_candidate_photo(client):
    recruiter = register_recruiter(client, email="photo-linked-recruiter@example.com")
    candidate = register_candidate(client, email="photo-linked-candidate@example.com", full_name="Photo Candidate")

    client.post(
        "/api/auth/me/photo",
        headers=auth_headers(candidate),
        files={"file": ("me.png", FAKE_PNG, "image/png")},
    )
    candidate_id = _me_id(client, candidate)

    job = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    )
    cv = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate),
        data={"candidate_name": "Photo Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    applied = client.post(
        "/api/applications",
        headers=auth_headers(candidate),
        json={
            "job_spec_id": job.json()["id"],
            "cv_id": cv.json()["id"],
            "contact_full_name": "Photo Candidate",
            "contact_email": "photo-linked-candidate@example.com",
            "contact_phone": "+44 7700 900666",
            "right_to_work_uk": True,
        },
    )
    assert applied.status_code == 201

    response = client.get(f"/api/auth/users/{candidate_id}/photo", headers=auth_headers(recruiter))
    assert response.status_code == 200
    assert response.content == FAKE_PNG
