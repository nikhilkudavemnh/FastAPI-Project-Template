from httpx import AsyncClient


async def test_register_login_refresh_me(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.io", "password": "password123", "full_name": "New"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "new@test.io"
    assert [role["name"] for role in body["roles"]] == ["user"]

    r = await client.post(
        "/api/v1/auth/login", data={"username": "new@test.io", "password": "password123"}
    )
    assert r.status_code == 200
    tokens = r.json()

    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "new@test.io"

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]

    # refresh token cannot be used as an access token
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


async def test_duplicate_register_conflict(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register", json={"email": "dup@test.io", "password": "password123"}
    )
    r = await client.post(
        "/api/v1/auth/register", json={"email": "dup@test.io", "password": "password123"}
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


async def test_bad_login(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/login", data={"username": "nobody@test.io", "password": "x"}
    )
    assert r.status_code == 401


async def test_unauthenticated(client: AsyncClient) -> None:
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401
