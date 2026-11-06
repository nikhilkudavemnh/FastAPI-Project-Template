from httpx import AsyncClient


async def test_admin_crud_users(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/users",
        json={"email": "crud@test.io", "password": "password123", "role_names": ["user"]},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    uid = r.json()["id"]

    r = await client.get("/api/v1/users", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = await client.patch(
        f"/api/v1/users/{uid}", json={"full_name": "Renamed"}, headers=admin_headers
    )
    assert r.status_code == 200 and r.json()["full_name"] == "Renamed"

    r = await client.delete(f"/api/v1/users/{uid}", headers=admin_headers)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/users/{uid}", headers=admin_headers)
    assert r.status_code == 404


async def test_regular_user_forbidden(client: AsyncClient, user_headers: dict[str, str]) -> None:
    r = await client.get("/api/v1/users", headers=user_headers)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"

    r = await client.get("/api/v1/users/me", headers=user_headers)
    assert r.status_code == 200
    r = await client.patch("/api/v1/users/me", json={"full_name": "Me"}, headers=user_headers)
    assert r.status_code == 200 and r.json()["full_name"] == "Me"


async def test_roles_and_permissions(
    client: AsyncClient, admin_headers: dict[str, str], user_headers: dict[str, str]
) -> None:
    r = await client.post(
        "/api/v1/roles",
        json={"name": "auditor", "permissions": ["users:read"]},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    role_id = r.json()["id"]

    me = (await client.get("/api/v1/users/me", headers=user_headers)).json()
    r = await client.post(f"/api/v1/users/{me['id']}/roles/{role_id}", headers=admin_headers)
    assert r.status_code == 200
    assert "auditor" in [x["name"] for x in r.json()["roles"]]

    # now the user can list users (users:read) but still not write
    r = await client.get("/api/v1/users", headers=user_headers)
    assert r.status_code == 200
    r = await client.post(
        "/api/v1/users",
        json={"email": "x@test.io", "password": "password123"},
        headers=user_headers,
    )
    assert r.status_code == 403

    r = await client.delete(f"/api/v1/users/{me['id']}/roles/{role_id}", headers=admin_headers)
    assert r.status_code == 200
    r = await client.get("/api/v1/users", headers=user_headers)
    assert r.status_code == 403


async def test_role_validation(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    r = await client.post("/api/v1/roles", json={"name": "Bad Name!"}, headers=admin_headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_failed"
