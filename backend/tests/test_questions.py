from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _create_gap_analysis(client, token: str) -> str:
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
    analysis_response = client.post(
        "/api/analysis/gap",
        headers=auth_headers(token),
        json={"cv_id": cv_response.json()["id"], "job_spec_id": job_response.json()["id"]},
    )
    assert analysis_response.status_code == 201
    return analysis_response.json()["id"]


def test_generate_questions_from_gap_analysis(client):
    token = register_recruiter(client, email="questions@example.com")
    analysis_id = _create_gap_analysis(client, token)

    generate_response = client.post(
        "/api/questions/generate",
        headers=auth_headers(token),
        json={"gap_analysis_id": analysis_id},
    )
    assert generate_response.status_code == 201
    plan = generate_response.json()

    assert plan["gap_analysis_id"] == analysis_id
    assert plan["candidate_name"] == "Alex Morgan"
    assert plan["job_title"] == "Senior Full Stack Engineer"
    assert len(plan["questions"]) >= 3
    assert plan["ai_question_count"] >= 3
    assert all(question["source"] == "AI" for question in plan["questions"])
    assert any("kubernetes" in question["text"].lower() or question["topic"] == "kubernetes" for question in plan["questions"])

    get_response = client.get(
        f"/api/questions/plans/by-analysis/{analysis_id}",
        headers=auth_headers(token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == plan["id"]


def test_add_custom_question_and_approve_toggle(client):
    token = register_recruiter(client, email="custom-questions@example.com")
    analysis_id = _create_gap_analysis(client, token)

    plan = client.post(
        "/api/questions/generate",
        headers=auth_headers(token),
        json={"gap_analysis_id": analysis_id},
    ).json()

    custom_response = client.post(
        "/api/questions/custom",
        headers=auth_headers(token),
        json={
            "plan_id": plan["id"],
            "text": "How would you design a retry strategy for interview session APIs?",
            "topic": "system design",
        },
    )
    assert custom_response.status_code == 201
    custom = custom_response.json()
    assert custom["source"] == "RECRUITER"
    assert custom["approved"] is True

    update_response = client.patch(
        f"/api/questions/{custom['id']}",
        headers=auth_headers(token),
        json={"approved": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["approved"] is False

    refreshed = client.get(
        f"/api/questions/plans/{plan['id']}",
        headers=auth_headers(token),
    ).json()
    assert refreshed["recruiter_question_count"] == 1
    assert refreshed["approved_count"] == refreshed["ai_question_count"]


def test_question_generation_requires_auth(client):
    response = client.post(
        "/api/questions/generate",
        json={"gap_analysis_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 401
