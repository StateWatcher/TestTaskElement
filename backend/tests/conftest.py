import os

os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret")
os.environ.setdefault("AUTH_SUPERUSER_LOGIN", "admin")
os.environ.setdefault("AUTH_SUPERUSER_PASSWORD", "admin-pass")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.session import get_session  # noqa: E402
from app.domain.enums import LotStatus  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, Lot, LotSet  # noqa: E402


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def transport(session_factory):
    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield ASGITransport(app=app)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest_asyncio.fixture
async def admin_client(transport):
    """Отдельный от `client` клиент с админской cookie-сессией."""
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        response = await test_client.post(
            "/api/auth/login", json={"login": "admin", "password": "admin-pass"}
        )
        assert response.status_code == 200
        yield test_client


def make_lot(set_id: int, external_id: str, **overrides) -> Lot:
    defaults = dict(
        set_id=set_id,
        external_id=external_id,
        project="ЖК Тест",
        address="ул. Тестовая, 1",
        rooms=1,
        area=30,
        floor=2,
        price=3_000_000,
        price_base=3_100_000,
        status=LotStatus.IN_SALE,
    )
    return Lot(**{**defaults, **overrides})


@pytest_asyncio.fixture
async def active_set(session_factory):
    """Активный набор с тремя лотами: студия и однушка в продаже, двушка продана."""
    async with session_factory() as session:
        lot_set = LotSet(name="feed.xml", is_active=True, lots_count=3)
        session.add(lot_set)
        await session.flush()
        lots = [
            make_lot(lot_set.id, "f1", rooms=0, area=20, price=2_000_000),
            make_lot(lot_set.id, "f2", rooms=1, area=40, price=3_000_000, project="ЖК Другой"),
            make_lot(lot_set.id, "f3", rooms=2, area=60, price=6_000_000, status=LotStatus.SOLD),
        ]
        session.add_all(lots)
        await session.commit()
        return {"set_id": lot_set.id, "lot_ids": [lot.id for lot in lots]}
