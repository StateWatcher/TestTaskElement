async def test_filter_by_rooms_and_project(client, active_set):
    by_rooms = (await client.get("/api/lots", params={"rooms": [0, 1]})).json()
    assert by_rooms["total"] == 2

    by_project = (await client.get("/api/lots", params={"project": "ЖК Другой"})).json()
    assert by_project["total"] == 1
    assert by_project["items"][0]["external_id"] == "f2"


async def test_filter_by_price_per_m2(client, active_set):
    # цены за м²: f1 = 100k, f2 = 75k, f3 = 100k
    response = (
        await client.get("/api/lots", params={"price_m2_min": 80_000, "price_m2_max": 120_000})
    ).json()
    assert {lot["external_id"] for lot in response["items"]} == {"f1", "f3"}


async def test_sort_and_paginate(client, active_set):
    page = (
        await client.get(
            "/api/lots", params={"sort": "area", "order": "desc", "page": 1, "page_size": 2}
        )
    ).json()
    assert page["total"] == 3
    assert [lot["external_id"] for lot in page["items"]] == ["f3", "f2"]


async def test_projects_list(client, active_set):
    projects = (await client.get("/api/lots/projects")).json()
    assert projects == ["ЖК Другой", "ЖК Тест"]


async def test_lot_from_inactive_set_hidden(client, session_factory, active_set):
    from app.models import LotSet
    from tests.conftest import make_lot

    async with session_factory() as session:
        stale = LotSet(name="old.xml")
        session.add(stale)
        await session.flush()
        hidden = make_lot(stale.id, "hidden")
        session.add(hidden)
        await session.commit()
        hidden_id = hidden.id

    assert (await client.get(f"/api/lots/{hidden_id}")).status_code == 404
    listing = (await client.get("/api/lots")).json()
    assert listing["total"] == 3


async def test_rest_and_jsonrpc_return_same_lots(client, active_set):
    rest = (await client.get("/api/lots", params={"sort": "price", "order": "asc"})).json()
    rpc = (
        await client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "lots.list",
                "params": {"sort": "price", "order": "asc"},
                "id": 7,
            },
        )
    ).json()["result"]
    assert rest == rpc
