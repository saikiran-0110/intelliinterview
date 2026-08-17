from tests.helpers import auth_headers, register_recruiter


def test_ai_draft_job_fills_requisition_fields(client):
    token = register_recruiter(client, email="ai-draft-recruiter@example.com")
    response = client.post(
        "/api/job-specs/ai-draft",
        headers=auth_headers(token),
        json={
            "prompt": (
                "Senior Platform Engineer in London, hybrid, 5+ years Kubernetes and Python, "
                "salary £80k-£100k, cloud infrastructure team"
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"]
    assert payload["description"]
    assert payload["salary_min_gbp"] is not None
    assert payload["salary_max_gbp"] is not None
    assert payload["employment_type"] in {"FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP"}
    assert payload["work_mode"] in {"ONSITE", "HYBRID", "REMOTE"}
