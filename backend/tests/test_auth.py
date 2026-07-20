async def test_login_wrong_password(client):
    response = await client.post("/api/auth/login", json={"login": "admin", "password": "nope"})
    assert response.status_code == 401


async def test_login_logout_flow(client):
    login = await client.post("/api/auth/login", json={"login": "admin", "password": "admin-pass"})
    assert login.status_code == 200
    assert login.json() == {"login": "admin"}

    me = await client.get("/api/auth/me")
    assert me.status_code == 200

    await client.post("/api/auth/logout")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_tampered_cookie_rejected(client):
    client.cookies.set("session", "forged-token")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_jsonrpc_admin_method_requires_auth(client):
    response = await client.post(
        "/api/jsonrpc",
        json={"jsonrpc": "2.0", "method": "admin.sets.list", "id": 1},
    )
    assert response.json()["error"]["code"] == -32001


async def test_jsonrpc_login_sets_cookie(client):
    response = await client.post(
        "/api/jsonrpc",
        json={
            "jsonrpc": "2.0",
            "method": "auth.login",
            "params": {"login": "admin", "password": "admin-pass"},
            "id": 1,
        },
    )
    assert response.json()["result"] == {"login": "admin"}

    listing = await client.post(
        "/api/jsonrpc", json={"jsonrpc": "2.0", "method": "admin.sets.list", "id": 2}
    )
    assert listing.json()["result"] == {"items": [], "total": 0, "page": 1, "page_size": 20}


async def test_jsonrpc_protocol_errors(client):
    unknown = await client.post(
        "/api/jsonrpc", json={"jsonrpc": "2.0", "method": "nope", "id": 1}
    )
    assert unknown.json()["error"]["code"] == -32601

    invalid = await client.post("/api/jsonrpc", json={"method": 42})
    assert invalid.json()["error"]["code"] == -32600

    bad_params = await client.post(
        "/api/jsonrpc",
        json={"jsonrpc": "2.0", "method": "lots.get", "params": {"lot_id": "abc"}, "id": 3},
    )
    assert bad_params.json()["error"]["code"] == -32602
