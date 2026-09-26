from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="rec-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Rec Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_session(client, recruiter_token: str, candidate_email: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Rec Candidate"},
        files={"file": ("rec-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
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
    session_response = client.post(
        "/api/sessions",
        headers=auth_headers(recruiter_token),
        json={
            "question_plan_id": plan_response.json()["id"],
            "candidate_email": candidate_email,
            "follow_up_limit": 1,
        },
    )
    assert session_response.status_code == 201
    return session_response.json()["id"]


def test_upload_then_fetch_round_trips(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate@example.com")

    upload = client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        data={"duration_seconds": "120"},
        files={"file": ("interview.webm", b"fake-video-bytes", "video/webm")},
    )
    assert upload.status_code == 201
    assert upload.json()["size_bytes"] == len(b"fake-video-bytes")
    assert upload.json()["duration_seconds"] == 120

    fetched = client.get(f"/api/sessions/{session_id}/recording", headers=auth_headers(candidate_token))
    assert fetched.status_code == 200
    assert fetched.content == b"fake-video-bytes"
    assert fetched.headers["content-type"].startswith("video/webm")

    recruiter_fetch = client.get(
        f"/api/sessions/{session_id}/recording", headers=auth_headers(recruiter_token)
    )
    assert recruiter_fetch.status_code == 200


def test_second_upload_replaces_the_first(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter2@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate2@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate2@example.com")

    client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        files={"file": ("first.webm", b"first-bytes", "video/webm")},
    )
    second = client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        files={"file": ("second.webm", b"second-bytes-longer", "video/webm")},
    )
    assert second.status_code == 201

    fetched = client.get(f"/api/sessions/{session_id}/recording", headers=auth_headers(candidate_token))
    assert fetched.content == b"second-bytes-longer"


def test_other_candidate_gets_404_on_upload_and_get(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter3@example.com")
    _register_candidate(client, email="rec-candidate3@example.com")
    other_token = _register_candidate(client, email="rec-other@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate3@example.com")

    upload = client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(other_token),
        files={"file": ("clip.webm", b"bytes", "video/webm")},
    )
    assert upload.status_code == 404

    get_response = client.get(f"/api/sessions/{session_id}/recording", headers=auth_headers(other_token))
    assert get_response.status_code == 404


def test_oversized_upload_is_rejected(client, monkeypatch):
    from app import config

    recruiter_token = register_recruiter(client, email="rec-recruiter4@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate4@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate4@example.com")

    monkeypatch.setattr(config.settings, "upload_max_size_mb", 0)

    response = client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        files={"file": ("clip.webm", b"some bytes that exceed a zero mb limit", "video/webm")},
    )
    assert response.status_code in (400, 413)


def test_disallowed_content_type_is_rejected(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter5@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate5@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate5@example.com")

    response = client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        files={"file": ("clip.exe", b"not a media file", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_get_recording_404_when_none_exists(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter6@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate6@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate6@example.com")

    response = client.get(f"/api/sessions/{session_id}/recording", headers=auth_headers(candidate_token))
    assert response.status_code == 404


def test_candidate_can_delete_their_own_recording(client):
    recruiter_token = register_recruiter(client, email="rec-recruiter7@example.com")
    candidate_token = _register_candidate(client, email="rec-candidate7@example.com")
    session_id = _create_session(client, recruiter_token, "rec-candidate7@example.com")

    client.post(
        f"/api/sessions/{session_id}/recording",
        headers=auth_headers(candidate_token),
        files={"file": ("clip.webm", b"bytes", "video/webm")},
    )
    delete_response = client.delete(
        f"/api/sessions/{session_id}/recording", headers=auth_headers(candidate_token)
    )
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/sessions/{session_id}/recording", headers=auth_headers(candidate_token))
    assert get_response.status_code == 404
