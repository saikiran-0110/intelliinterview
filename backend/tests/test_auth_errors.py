from tests.helpers import auth_headers, register_candidate, register_recruiter


def test_duplicate_register_returns_conflict(client):
    register_recruiter(client, email="dup@example.com")
    response = client.post(
        "/api/auth/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "full_name": "Other",
            "role": "RECRUITER",
        },
    )
    assert response.status_code == 409


def test_login_rejects_invalid_credentials(client):
    register_recruiter(client, email="login-fail@example.com")
    missing = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert missing.status_code == 401
    wrong = client.post("/api/auth/login", json={"email": "login-fail@example.com", "password": "not-the-password"})
    assert wrong.status_code == 401


def test_me_requires_valid_token_and_returns_profile(client):
    unauthenticated = client.get("/api/auth/me")
    assert unauthenticated.status_code == 401

    invalid = client.get("/api/auth/me", headers=auth_headers("not-a-jwt"))
    assert invalid.status_code == 401

    token = register_recruiter(client, email="me-user@example.com")
    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == "me-user@example.com"
    assert me.json()["role"] == "RECRUITER"


def test_update_profile(client):
    token = register_candidate(client, email="profile@example.com", full_name="Old Name")
    response = client.patch(
        "/api/auth/me",
        headers=auth_headers(token),
        json={
            "full_name": "New Name",
            "phone": "+44 7700 900999",
            "location": "Leeds, UK",
            "linkedin_url": "https://linkedin.com/in/new",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["full_name"] == "New Name"
    assert payload["phone"] == "+44 7700 900999"
    assert payload["location"] == "Leeds, UK"


def test_candidate_cannot_access_recruiter_bias(client):
    token = register_candidate(client, email="bias-blocked@example.com")
    response = client.get("/api/bias/overview", headers=auth_headers(token))
    assert response.status_code == 403


def test_register_start_requires_company_for_recruiter(client):
    response = client.post(
        "/api/auth/register/start",
        json={
            "email": "nocompany@example.com",
            "password": "password123",
            "full_name": "No Company",
            "role": "RECRUITER",
            "phone": "+44 7700 900111",
        },
    )
    assert response.status_code == 400


def test_login_start_unknown_email(client):
    response = client.post("/api/auth/login/start", json={"email": "missing@example.com"})
    assert response.status_code == 404


def test_otp_verify_without_challenge(client):
    response = client.post(
        "/api/auth/otp/verify",
        json={"email": "nobody@example.com", "otp": "123456", "purpose": "LOGIN"},
    )
    assert response.status_code == 400


def test_otp_verify_rejects_wrong_code(client, monkeypatch):
    monkeypatch.setattr("app.services.otp.secrets.randbelow", lambda _n: 111111)
    start = client.post(
        "/api/auth/register/start",
        json={
            "email": "wrong-otp@example.com",
            "password": "password123",
            "full_name": "Wrong OTP",
            "role": "CANDIDATE",
            "phone": "+44 7700 900222",
        },
    )
    assert start.status_code == 200
    verify = client.post(
        "/api/auth/otp/verify",
        json={"email": "wrong-otp@example.com", "otp": "000000", "purpose": "REGISTER"},
    )
    assert verify.status_code == 400


def test_register_start_conflict_when_email_exists(client):
    register_recruiter(client, email="exists@example.com")
    response = client.post(
        "/api/auth/register/start",
        json={
            "email": "exists@example.com",
            "password": "password123",
            "full_name": "Already Here",
            "role": "RECRUITER",
            "phone": "+44 7700 900333",
            "company": "Acme",
        },
    )
    assert response.status_code == 409
