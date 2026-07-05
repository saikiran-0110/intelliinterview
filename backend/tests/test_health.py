def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "UP"
    assert payload["application"] == "IntelliInterview"


def test_register_and_login(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "recruiter@example.com",
            "password": "password123",
            "full_name": "Recruiter One",
            "role": "RECRUITER",
        },
    )
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["email"] == "recruiter@example.com"
    assert register_payload["role"] == "RECRUITER"
    assert register_payload["token"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": "recruiter@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"]
