from tests.conftest import register_and_login


def test_register_creates_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"full_name": "Jane Doe", "email": "jane@test.local", "password": "StrongPass123!", "role": "ENUMERATOR"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "jane@test.local"
    assert "hashed_password" not in body


def test_duplicate_registration_rejected(client):
    payload = {"full_name": "Jane Doe", "email": "dupe@test.local", "password": "StrongPass123!", "role": "ENUMERATOR"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_with_wrong_password_fails(client):
    client.post(
        "/api/auth/register",
        json={"full_name": "Jane Doe", "email": "wrongpw@test.local", "password": "StrongPass123!", "role": "ENUMERATOR"},
    )
    resp = client.post("/api/auth/login-json", json={"email": "wrongpw@test.local", "password": "nope"})
    assert resp.status_code == 401


def test_login_returns_token(client):
    client.post(
        "/api/auth/register",
        json={"full_name": "Jane Doe", "email": "login@test.local", "password": "StrongPass123!", "role": "ENUMERATOR"},
    )
    resp = client.post("/api/auth/login-json", json={"email": "login@test.local", "password": "StrongPass123!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_requires_valid_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401

    headers = register_and_login(client)
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMINISTRATOR"


def test_logout_revokes_token(client):
    headers = register_and_login(client, email="logout@test.local")
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 204

    # The same token must now be rejected.
    resp2 = client.get("/api/auth/me", headers=headers)
    assert resp2.status_code == 401
