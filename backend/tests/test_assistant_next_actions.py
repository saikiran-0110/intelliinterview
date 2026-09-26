from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_JOB_SPEC


def _create_open_job(client, recruiter_token, title="Platform Engineer"):
    response = client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={
            "title": title,
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
    assert response.status_code == 201
    return response.json()


def test_next_actions_empty_pipeline_returns_nothing_blocked(client):
    recruiter_token = register_recruiter(client, email="na-empty@example.com")

    response = client.get("/api/assistant/next-actions", headers=auth_headers(recruiter_token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_from"] == "pipeline-rules"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == "nothing-blocked"


def test_next_actions_flags_open_role_with_no_applications(client):
    recruiter_token = register_recruiter(client, email="na-openrole@example.com")
    _create_open_job(client, recruiter_token, title="Backend Engineer")

    response = client.get("/api/assistant/next-actions", headers=auth_headers(recruiter_token))

    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["id"] == "open-roles-no-applications" for item in items)
    match = next(item for item in items if item["id"] == "open-roles-no-applications")
    assert "1 open role" in match["title"]
    assert match["cta_path"] == "/recruiter/jobs"


def test_next_actions_requires_auth(client):
    response = client.get("/api/assistant/next-actions")
    assert response.status_code == 401
