from datetime import datetime, timedelta, timezone


def register_recruiter(client, email="recruiter@example.com", password="password123"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Recruiter One",
            "role": "RECRUITER",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["token"]


def register_candidate(client, email="candidate@example.com", password="password123", full_name="Alex Candidate"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def confirm_session_for_interview(client, recruiter_token: str, session_id: str) -> None:
    starts_at = datetime.now(timezone.utc) + timedelta(minutes=1)
    response = client.post(
        f"/api/scheduling/{session_id}/force-schedule",
        headers=auth_headers(recruiter_token),
        json={
            "starts_at": starts_at.isoformat(),
            "duration_minutes": 45,
            "notify_candidate": False,
        },
    )
    assert response.status_code == 200
