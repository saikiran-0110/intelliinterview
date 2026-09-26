from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.calendar_export import build_ics, google_calendar_url, outlook_calendar_url
from tests.helpers import auth_headers, register_recruiter
from tests.sample_documents import SAMPLE_CV, SAMPLE_JOB_SPEC


def _register_candidate(client, email="cal-candidate@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Cal Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _create_confirmed_session(client, recruiter_token: str, candidate_email: str) -> str:
    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Cal Candidate"},
        files={"file": ("cal-cv.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
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
    session_id = session_response.json()["id"]

    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    force = client.post(
        f"/api/scheduling/{session_id}/force-schedule",
        headers=auth_headers(recruiter_token),
        json={"starts_at": starts_at.isoformat(), "duration_minutes": 45, "notify_candidate": False},
    )
    assert force.status_code == 200
    return session_id


def test_build_ics_contains_vevent_and_utc_dtstart():
    session_id = uuid4()
    scheduled_at = datetime(2026, 5, 1, 14, 30, tzinfo=timezone.utc)
    ics = build_ics(
        session_id=session_id,
        scheduled_at=scheduled_at,
        duration_minutes=45,
        job_title="Backend Engineer",
        candidate_name="Alex Morgan",
        recruiter_email="recruiter@example.com",
        candidate_email="alex@example.com",
        portal_url="http://localhost:5173/candidate/interview/abc",
    )
    assert "BEGIN:VEVENT" in ics
    assert "DTSTART:20260501T143000Z" in ics
    assert "DTEND:20260501T151500Z" in ics
    assert f"UID:{session_id}@intelliinterview" in ics
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-PT15M" in ics


def test_build_ics_escapes_commas_in_text_fields():
    ics = build_ics(
        session_id=uuid4(),
        scheduled_at=datetime.now(timezone.utc),
        duration_minutes=45,
        job_title="Engineer, Platform",
        candidate_name="Smith, Jordan",
        recruiter_email="recruiter@example.com",
        candidate_email="jordan@example.com",
        portal_url="http://localhost:5173/candidate/interview/abc",
    )
    assert "Engineer\\, Platform" in ics
    assert "Smith\\, Jordan" in ics


def test_google_and_outlook_urls_are_public_templates():
    scheduled_at = datetime(2026, 5, 1, 14, 30, tzinfo=timezone.utc)
    google_url = google_calendar_url(scheduled_at, 45, "Backend Engineer", "Alex Morgan", "http://portal")
    outlook_url = outlook_calendar_url(scheduled_at, 45, "Backend Engineer", "Alex Morgan", "http://portal")
    assert google_url.startswith("https://calendar.google.com/calendar/render?")
    assert outlook_url.startswith("https://outlook.live.com/calendar/0/deeplink/compose?")


def test_calendar_ics_download_for_recruiter_and_candidate(client):
    recruiter_token = register_recruiter(client, email="cal-recruiter@example.com")
    candidate_token = _register_candidate(client, email="cal-candidate@example.com")
    session_id = _create_confirmed_session(client, recruiter_token, "cal-candidate@example.com")

    recruiter_response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar.ics", headers=auth_headers(recruiter_token)
    )
    assert recruiter_response.status_code == 200
    assert recruiter_response.headers["content-type"].startswith("text/calendar")
    assert "attachment" in recruiter_response.headers["content-disposition"]
    assert "BEGIN:VEVENT" in recruiter_response.text

    candidate_response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar.ics", headers=auth_headers(candidate_token)
    )
    assert candidate_response.status_code == 200


def test_calendar_ics_other_candidate_gets_404(client):
    recruiter_token = register_recruiter(client, email="cal-recruiter2@example.com")
    _register_candidate(client, email="cal-candidate2@example.com")
    other_candidate_token = _register_candidate(client, email="cal-other@example.com")
    session_id = _create_confirmed_session(client, recruiter_token, "cal-candidate2@example.com")

    response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar.ics", headers=auth_headers(other_candidate_token)
    )
    assert response.status_code == 404


def test_calendar_links_response_shape(client):
    recruiter_token = register_recruiter(client, email="cal-recruiter3@example.com")
    _register_candidate(client, email="cal-candidate3@example.com")
    session_id = _create_confirmed_session(client, recruiter_token, "cal-candidate3@example.com")

    response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar-links", headers=auth_headers(recruiter_token)
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["google_url"].startswith("https://calendar.google.com/")
    assert payload["outlook_url"].startswith("https://outlook.live.com/")
    assert payload["ics_url"] == f"/api/scheduling/sessions/{session_id}/calendar.ics"


def test_calendar_endpoints_return_400_without_scheduled_at(client):
    recruiter_token = register_recruiter(client, email="cal-recruiter4@example.com")
    _register_candidate(client, email="cal-candidate4@example.com")

    cv_response = client.post(
        "/api/cvs/upload",
        headers=auth_headers(recruiter_token),
        data={"candidate_name": "Cal Candidate"},
        files={"file": ("cal-cv2.txt", SAMPLE_CV.encode("utf-8"), "text/plain")},
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
            "candidate_email": "cal-candidate4@example.com",
            "follow_up_limit": 1,
        },
    )
    session_id = session_response.json()["id"]

    ics_response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar.ics", headers=auth_headers(recruiter_token)
    )
    assert ics_response.status_code == 400

    links_response = client.get(
        f"/api/scheduling/sessions/{session_id}/calendar-links", headers=auth_headers(recruiter_token)
    )
    assert links_response.status_code == 400
