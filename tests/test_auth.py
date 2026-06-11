from tests.conftest import auth_headers, create_user


def test_register_login_and_refresh(client):
    create_user(client, "candidate@example.com", "candidate")

    login = client.post("/auth/login", json={"email": "candidate@example.com", "password": "password123"})
    assert login.status_code == 200
    body = login.json()
    assert body["access_token"]
    assert body["refresh_token"]

    refresh = client.post("/auth/refresh", params={"refresh_token": body["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_rbac_blocks_candidate_from_recruiter_endpoint(client):
    create_user(client, "candidate@example.com", "candidate")
    response = client.post(
        "/recruiter/companies",
        json={"name": "Acme"},
        headers=auth_headers(client, "candidate@example.com"),
    )
    assert response.status_code == 403
