CONTACT = {"name": "Иван", "contact": "+79990000000"}


async def test_create_request_without_lot(client):
    response = await client.post(
        "/api/requests", json={**CONTACT, "comment": "Интересует ипотека"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "new"
    assert body["lot_id"] is None
    assert body["lot"] is None


async def test_create_request_with_lot(client, active_set):
    lot_id = active_set["lot_ids"][0]
    response = await client.post(
        "/api/requests", json={"lot_id": lot_id, **CONTACT, "comment": "Хочу посмотреть лот"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["lot_id"] == lot_id
    assert body["lot"]["id"] == lot_id


async def test_create_request_unknown_lot(client):
    response = await client.post(
        "/api/requests", json={"lot_id": 10_000, **CONTACT, "comment": "Комментарий"}
    )
    assert response.status_code == 404


async def test_requests_list_admin_only(client, admin_client):
    assert (await client.get("/api/requests")).status_code == 401

    await client.post("/api/requests", json={**CONTACT, "comment": "Комментарий"})
    listing = (await admin_client.get("/api/requests")).json()
    assert listing["total"] == 1


async def test_set_request_status(client, admin_client):
    created = (
        await client.post("/api/requests", json={**CONTACT, "comment": "Комментарий"})
    ).json()

    in_progress = await admin_client.patch(
        f"/api/requests/{created['id']}", json={"status": "in_progress"}
    )
    assert in_progress.json()["status"] == "in_progress"

    closed = await admin_client.patch(
        f"/api/requests/{created['id']}", json={"status": "closed"}
    )
    assert closed.json()["status"] == "closed"


async def test_set_status_unknown_request(admin_client):
    response = await admin_client.patch("/api/requests/10000", json={"status": "closed"})
    assert response.status_code == 404


async def test_rest_and_jsonrpc_return_same_requests(client, admin_client, active_set):
    lot_id = active_set["lot_ids"][0]
    await client.post(
        "/api/requests", json={"lot_id": lot_id, **CONTACT, "comment": "Комментарий"}
    )

    rest = (await admin_client.get("/api/requests")).json()
    rpc = (
        await admin_client.post(
            "/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "admin.requests.list", "id": 1},
        )
    ).json()["result"]
    assert rest == rpc
