import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import get_session
from app.domain.enums import BookingStatus, LotStatus
from app.main import app
from app.models import Base, Booking, Lot, LotSet

CONTACT = {"name": "Иван", "contact": "+79990000000"}


async def test_booking_flow(client, admin_client, active_set):
    lot_id = active_set["lot_ids"][0]

    created = await client.post("/api/bookings", json={"lot_id": lot_id, **CONTACT})
    assert created.status_code == 201
    booking = created.json()
    assert booking["status"] == "active"
    assert booking["lot"]["status"] == "booked"

    # уже забронированный лот забронировать нельзя
    conflict = await client.post("/api/bookings", json={"lot_id": lot_id, **CONTACT})
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "lot_not_available"

    # отмена возвращает лот в продажу
    cancelled = await admin_client.post(f"/api/bookings/{booking['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    lot = (await client.get(f"/api/lots/{lot_id}")).json()
    assert lot["status"] == "in_sale"


async def test_cannot_book_sold_lot(client, active_set):
    sold_lot_id = active_set["lot_ids"][2]
    response = await client.post("/api/bookings", json={"lot_id": sold_lot_id, **CONTACT})
    assert response.status_code == 409


async def test_cannot_book_unknown_lot(client, active_set):
    response = await client.post("/api/bookings", json={"lot_id": 10_000, **CONTACT})
    assert response.status_code == 404


async def test_booking_conflict_via_jsonrpc(client, active_set):
    lot_id = active_set["lot_ids"][0]

    def rpc_payload(request_id):
        return {
            "jsonrpc": "2.0",
            "method": "bookings.create",
            "params": {"lot_id": lot_id, **CONTACT},
            "id": request_id,
        }

    first = (await client.post("/api/jsonrpc", json=rpc_payload(1))).json()
    assert first["result"]["status"] == "active"

    second = (await client.post("/api/jsonrpc", json=rpc_payload(2))).json()
    assert second["error"]["code"] == -32003
    assert second["error"]["data"]["code"] == "lot_not_available"


async def test_concurrent_booking_requests_only_one_succeeds(tmp_path):
    """Настоящая гонка: 5 одновременных запросов на один лот через asyncio.gather.

    Использует файловую SQLite (не in-memory StaticPool, как остальные тесты):
    StaticPool даёт всем сессиям одно физическое соединение, а SQLite не умеет
    вести на нём по-настоящему параллельные транзакции — под ним тест давал
    ложные результаты (то 5 успешных броней, то потерянный commit), не отражающие
    поведение сервиса, а только неспособность StaticPool изображать конкурентность.
    С отдельными файловыми соединениями каждая из 5 задач получает реальную,
    независимую транзакцию — то, чему подвергается прод под Postgres.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'concurrency.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with session_factory() as session:
            lot_set = LotSet(name="feed.xml", is_active=True, lots_count=1)
            session.add(lot_set)
            await session.flush()
            lot = Lot(
                set_id=lot_set.id,
                external_id="f1",
                project="ЖК Тест",
                address="ул. Тестовая, 1",
                rooms=1,
                area=30,
                floor=2,
                price=3_000_000,
                price_base=3_100_000,
                status=LotStatus.IN_SALE,
            )
            session.add(lot)
            await session.commit()
            lot_id = lot.id

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            responses = await asyncio.gather(
                *(
                    client.post("/api/bookings", json={"lot_id": lot_id, **CONTACT})
                    for _ in range(5)
                )
            )

            assert sorted(r.status_code for r in responses) == [201, 409, 409, 409, 409]

            lot_out = (await client.get(f"/api/lots/{lot_id}")).json()
            assert lot_out["status"] == "booked"

        async with session_factory() as session:
            active = (
                await session.execute(
                    select(Booking).where(
                        Booking.lot_id == lot_id, Booking.status == BookingStatus.ACTIVE
                    )
                )
            ).scalars().all()
            assert len(active) == 1
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


async def test_bookings_list_admin_only(client, admin_client, active_set):
    assert (await client.get("/api/bookings")).status_code == 401

    await client.post("/api/bookings", json={"lot_id": active_set["lot_ids"][0], **CONTACT})
    listing = (await admin_client.get("/api/bookings")).json()
    assert listing["total"] == 1
    assert listing["items"][0]["lot"]["id"] == active_set["lot_ids"][0]
