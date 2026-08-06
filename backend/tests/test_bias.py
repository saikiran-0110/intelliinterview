from tests.helpers import auth_headers, register_recruiter


def test_bias_overview_returns_advisory_alerts(client):
    recruiter_token = register_recruiter(client, email="bias-recruiter@example.com")
    response = client.get("/api/bias/overview", headers=auth_headers(recruiter_token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["alert_count"] >= 1
    assert payload["notes"]
    assert payload["alerts"][0]["title"]
