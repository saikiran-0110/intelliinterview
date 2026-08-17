def test_otp_register_and_login(client, monkeypatch):
    monkeypatch.setattr("app.services.otp.secrets.randbelow", lambda _n: 123456)

    start = client.post(
        "/api/auth/register/start",
        json={
            "email": "otp-recruiter@example.com",
            "password": "password123",
            "full_name": "OTP Recruiter",
            "role": "RECRUITER",
            "phone": "+44 7700 900111",
            "company": "OTP Hiring Ltd",
            "job_title": "Hiring Manager",
            "location": "London, UK",
        },
    )
    assert start.status_code == 200
    assert "dev_otp" not in start.json()

    verify = client.post(
        "/api/auth/otp/verify",
        json={
            "email": "otp-recruiter@example.com",
            "otp": "123456",
            "purpose": "REGISTER",
        },
    )
    assert verify.status_code == 200
    assert verify.json()["token"]
    assert verify.json()["company"] == "OTP Hiring Ltd"
    assert verify.json()["email_verified"] is True

    login_start = client.post("/api/auth/login/start", json={"email": "otp-recruiter@example.com"})
    assert login_start.status_code == 200
    assert "dev_otp" not in login_start.json()

    login_verify = client.post(
        "/api/auth/otp/verify",
        json={
            "email": "otp-recruiter@example.com",
            "otp": "123456",
            "purpose": "LOGIN",
        },
    )
    assert login_verify.status_code == 200
    assert login_verify.json()["token"]
