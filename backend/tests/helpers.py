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


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
