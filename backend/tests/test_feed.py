import base64

import pytest

from app.domain.errors import FeedParseError
from app.services.feed import parse_feed

FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed>
  <object>
    <name>ЖК Тест</name>
    <address>ул. Общая, 1</address>
    <buildings>
      <building>
        <address>ул. Корпусная, 1</address>
        <flats>
          <flat>
            <flat_id>f1</flat_id><status>FREE</status><room>1</room>
            <area>30.5</area><floor>2</floor>
            <price>3000000</price><price_base>3100000</price_base>
          </flat>
          <flat>
            <flat_id>f2</flat_id><status>SOLD</status><room>2</room>
            <area>50</area><floor>3</floor>
            <price>5000000</price><price_base>5000000</price_base>
          </flat>
          <flat>
            <flat_id>broken</flat_id><status>FREE</status><room>не число</room>
            <area>10</area><floor>1</floor>
            <price>1</price><price_base>1</price_base>
          </flat>
        </flats>
      </building>
    </buildings>
  </object>
</feed>
"""


def test_parse_feed_maps_fields():
    rows, skipped = parse_feed(FEED_XML.encode())
    assert skipped == 1  # лот с нечисловой комнатностью пропущен
    assert len(rows) == 2
    first = rows[0]
    assert first["external_id"] == "f1"
    assert first["project"] == "ЖК Тест"
    assert first["address"] == "ул. Корпусная, 1"
    assert first["rooms"] == 1
    assert first["status"] == "in_sale"
    assert rows[1]["status"] == "sold"


def test_parse_feed_tolerates_junk_prefix():
    # реальный element.xml начинается с "//" перед xml-декларацией
    rows, _ = parse_feed(b"//" + FEED_XML.encode())
    assert len(rows) == 2


def test_parse_feed_rejects_invalid_xml():
    with pytest.raises(FeedParseError):
        parse_feed(b"not xml at all")


def test_parse_feed_rejects_wrong_root():
    with pytest.raises(FeedParseError):
        parse_feed(b"<catalog></catalog>")


async def test_upload_and_activate_flow(admin_client):
    # без активного набора витрина пуста
    empty = (await admin_client.get("/api/lots")).json()
    assert empty["total"] == 0

    upload = await admin_client.post(
        "/api/sets", files={"file": ("feed.xml", FEED_XML.encode(), "text/xml")}
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["set"]["lots_count"] == 2
    assert body["skipped"] == 1
    assert body["set"]["is_active"] is False

    set_id = body["set"]["id"]
    activate = await admin_client.post(f"/api/sets/{set_id}/activate")
    assert activate.status_code == 200
    assert activate.json()["is_active"] is True

    lots = (await admin_client.get("/api/lots")).json()
    assert lots["total"] == 2
    assert lots["items"][0]["price_per_m2"] is not None


async def test_upload_requires_auth(client):
    response = await client.post(
        "/api/sets", files={"file": ("feed.xml", FEED_XML.encode(), "text/xml")}
    )
    assert response.status_code == 401


async def test_sets_list_paginated(admin_client):
    for _ in range(3):
        await admin_client.post(
            "/api/sets", files={"file": ("feed.xml", FEED_XML.encode(), "text/xml")}
        )

    page = (await admin_client.get("/api/sets", params={"page": 2, "page_size": 1})).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1

    # наборы отдаются от свежих к старым, страницы не пересекаются
    ids = [
        (await admin_client.get("/api/sets", params={"page": n, "page_size": 1})).json()["items"][
            0
        ]["id"]
        for n in (1, 2, 3)
    ]
    assert ids == sorted(ids, reverse=True)


async def test_rest_and_jsonrpc_return_same_sets(admin_client):
    await admin_client.post(
        "/api/sets", files={"file": ("feed.xml", FEED_XML.encode(), "text/xml")}
    )

    rest = (await admin_client.get("/api/sets", params={"page": 1, "page_size": 20})).json()
    rpc = (
        await admin_client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "admin.sets.list",
                "params": {"page": 1, "page_size": 20},
                "id": 1,
            },
        )
    ).json()["result"]
    assert rest == rpc


async def test_upload_via_jsonrpc(admin_client):
    response = await admin_client.post(
        "/api/jsonrpc",
        json={
            "jsonrpc": "2.0",
            "method": "admin.sets.upload",
            "params": {
                "filename": "feed.xml",
                "content_base64": base64.b64encode(FEED_XML.encode()).decode(),
            },
            "id": 1,
        },
    )
    result = response.json()["result"]
    assert result["set"]["lots_count"] == 2
