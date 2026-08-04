from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_JOB_SPEC


def test_analytics_overview_returns_structure(client):
    recruiter_token = register_recruiter(client, email="analytics-recruiter@example.com")
    client.post(
        "/api/job-specs",
        headers=auth_headers(recruiter_token),
        json={"title": "Platform Engineer", "description": SAMPLE_JOB_SPEC},
    )
    response = client.get("/api/analytics/overview", headers=auth_headers(recruiter_token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_roles"] >= 1
    assert "applications_per_role" in payload
    assert "pipeline_stages" in payload
    assert "open_positions" in payload
    assert any(item["job_title"] == "Platform Engineer" for item in payload["applications_per_role"])
