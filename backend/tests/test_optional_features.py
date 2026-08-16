from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="opt-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Optional Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def test_recruiter_job_requisition_and_candidate_apply_flow(client):
    recruiter_token = register_recruiter(client, email="req-recruiter@example.com")
    candidate_token = _register_candidate(client, email="req-candidate@example.com")

    job = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={
            "title": "Platform Engineer",
            "description": SAMPLE_JOB_SPEC,
            "department": "Engineering",
            "location": "London, UK",
            "employment_type": "FULL_TIME",
            "work_mode": "HYBRID",
            "salary_min_gbp": 65000,
            "salary_max_gbp": 85000,
            "years_experience_min": 3,
            "benefits": "Pension, private healthcare, 25 days holiday",
            "is_open": True,
        },
    )
    assert job.status_code == 201
    payload = job.json()
    assert payload["salary_min_gbp"] == 65000
    assert payload["salary_max_gbp"] == 85000
    assert payload["location"] == "London, UK"
    job_id = payload["id"]

    open_jobs = client.get("/api/job-specs/open", headers=auth_headers(candidate_token))
    assert open_jobs.status_code == 200
    assert any(item["id"] == job_id for item in open_jobs.json())

    cv = client.post(
        "/api/cvs/upload",
        headers=auth_headers(candidate_token),
        data={"candidate_name": "Optional Candidate"},
        files={"file": ("cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
    )
    assert cv.status_code == 201
    cv_id = cv.json()["id"]

    preview = client.post(
        "/api/applications/match-preview",
        headers=auth_headers(candidate_token),
        json={"job_spec_id": job_id, "cv_id": cv_id},
    )
    assert preview.status_code == 200
    assert preview.json()["match_score"] is not None
    assert preview.json()["plain_language_breakdown"]

    apply = client.post(
        "/api/applications",
        headers=auth_headers(candidate_token),
        json={
            "job_spec_id": job_id,
            "cv_id": cv_id,
            "contact_full_name": "Optional Candidate",
            "contact_email": "req-candidate@example.com",
            "contact_phone": "+44 7700 900123",
            "current_location": "Manchester, UK",
            "expected_salary_gbp": 72000,
            "right_to_work_uk": True,
            "cover_note": "Excited to join the platform team.",
        },
    )
    assert apply.status_code == 201
    assert apply.json()["stage"] == "APPLIED"
    assert apply.json()["match_score"] is not None
    assert apply.json()["contact_phone"] == "+44 7700 900123"
    assert apply.json()["expected_salary_gbp"] == 72000

    ranking = client.get(f"/api/ranking/{job_id}", headers=auth_headers(recruiter_token))
    assert ranking.status_code == 200
    assert ranking.json()["candidates"]
