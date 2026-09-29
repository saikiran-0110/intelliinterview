from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def test_upload_cv_and_create_job_spec(client):
    token = register_recruiter(client)

    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        data={"candidate_name": "Alex Morgan"},
        files={"file": ("alex-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert cv_response.status_code == 201
    cv_payload = cv_response.json()
    assert cv_payload["candidate_name"] == "Alex Morgan"
    assert "python" in cv_payload["parsed_profile"]["skills"]
    assert cv_payload["parsed_profile"]["years_experience"] == 6

    job_response = client.post(
        "/api/job-specs",
        headers=auth_headers(token),
        json={
            "title": "Senior Full Stack Engineer",
            "description": SAMPLE_JOB_SPEC,
        },
    )
    assert job_response.status_code == 201
    job_payload = job_response.json()
    assert job_payload["title"] == "Senior Full Stack Engineer"
    assert "fastapi" in job_payload["parsed_requirements"]["required_skills"]
    assert job_payload["parsed_requirements"]["years_experience_required"] == 5


def test_gap_analysis_end_to_end(client):
    token = register_recruiter(client, email="gap-recruiter@example.com")

    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        data={"candidate_name": "Alex Morgan"},
        files={"file": ("alex-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    job_response = client.post(
        "/api/job-specs",
        headers=auth_headers(token),
        json={
            "title": "Senior Full Stack Engineer",
            "description": SAMPLE_JOB_SPEC,
        },
    )
    cv_id = cv_response.json()["id"]
    job_spec_id = job_response.json()["id"]

    analysis_response = client.post(
        "/api/analysis/gap",
        headers=auth_headers(token),
        json={"cv_id": cv_id, "job_spec_id": job_spec_id},
    )
    assert analysis_response.status_code == 201
    payload = analysis_response.json()

    assert payload["candidate_name"] == "Alex Morgan"
    assert payload["job_title"] == "Senior Full Stack Engineer"
    assert payload["strong_match_count"] >= 3
    assert payload["gap_count"] >= 1
    assert payload["match_score"] is not None
    assert payload["narrative_summary"]
    assert payload["experience_analysis"]["alignment"] in {"strong", "partial", "gap", "unknown"}
    gap_and_partial = [item["name"] for item in payload["gaps"]] + [
        item["name"] for item in payload["partial_matches"]
    ]
    assert "kubernetes" in gap_and_partial

    get_response = client.get(f"/api/analysis/gap/{payload['id']}", headers=auth_headers(token))
    assert get_response.status_code == 200
    assert get_response.json()["id"] == payload["id"]


def test_gap_analysis_requires_auth(client):
    response = client.post(
        "/api/analysis/gap",
        json={"cv_id": "00000000-0000-0000-0000-000000000001", "job_spec_id": "00000000-0000-0000-0000-000000000002"},
    )
    assert response.status_code == 401


def test_list_gap_analyses_collapses_duplicate_cv_job_pairs(client):
    token = register_recruiter(client, email="gap-dedupe-recruiter@example.com")

    cv_id = client.post(
        "/api/cvs/upload",
        headers=auth_headers(token),
        data={"candidate_name": "Alex Morgan"},
        files={"file": ("alex-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    ).json()["id"]
    job_spec_id = client.post(
        "/api/job-specs",
        headers=auth_headers(token),
        json={"title": "Senior Full Stack Engineer", "description": SAMPLE_JOB_SPEC},
    ).json()["id"]

    first = client.post(
        "/api/analysis/gap",
        headers=auth_headers(token),
        json={"cv_id": cv_id, "job_spec_id": job_spec_id},
    ).json()
    second = client.post(
        "/api/analysis/gap",
        headers=auth_headers(token),
        json={"cv_id": cv_id, "job_spec_id": job_spec_id},
    ).json()
    assert first["id"] != second["id"]

    listed = client.get("/api/analysis/gap", headers=auth_headers(token)).json()
    matching = [item for item in listed if item["cv_id"] == cv_id and item["job_spec_id"] == job_spec_id]
    assert len(matching) == 1
    assert matching[0]["id"] in {first["id"], second["id"]}


def test_applying_for_a_job_reuses_an_existing_gap_analysis(client):
    from tests.helpers import register_candidate

    recruiter = register_recruiter(client, email="gap-reuse-recruiter@example.com")
    candidate = register_candidate(client, email="gap-reuse-candidate@example.com", full_name="Alex Morgan")

    job_id = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC, "is_open": True},
    ).json()["id"]
    cv_id = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate),
        data={"candidate_name": "Alex Morgan"},
        files={"file": ("alex-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    ).json()["id"]

    preview = client.post(
        "/api/applications/match-preview",
        headers=auth_headers(candidate),
        json={"job_spec_id": job_id, "cv_id": cv_id},
    )
    assert preview.status_code == 200

    applied = client.post(
        "/api/applications",
        headers=auth_headers(candidate),
        json={
            "job_spec_id": job_id,
            "cv_id": cv_id,
            "contact_full_name": "Alex Morgan",
            "contact_email": "gap-reuse-candidate@example.com",
            "contact_phone": "+44 7700 900123",
            "right_to_work_uk": True,
        },
    )
    assert applied.status_code == 201

    listed = client.get("/api/analysis/gap", headers=auth_headers(recruiter)).json()
    matching = [item for item in listed if item["cv_id"] == cv_id and item["job_spec_id"] == job_id]
    assert len(matching) == 1
    assert applied.json()["gap_analysis_id"] == matching[0]["id"]
