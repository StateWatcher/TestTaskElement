from typing import Any

from sqlalchemy import ColumnElement, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import LotStatus
from app.models import Lot
from app.schemas.lot import LotFilters, LotSortField, SortOrder

_SORT_COLUMNS: dict[LotSortField, ColumnElement] = {
    LotSortField.PRICE: Lot.price,
    LotSortField.PRICE_PER_M2: Lot.price_per_m2,
    LotSortField.AREA: Lot.area,
    LotSortField.FLOOR: Lot.floor,
    LotSortField.ROOMS: Lot.rooms,
}


class LotRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, lot_id: int) -> Lot | None:
        return await self._session.get(Lot, lot_id)

    async def get_for_update(self, lot_id: int) -> Lot | None:
        result = await self._session.execute(
            select(Lot).where(Lot.id == lot_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def try_book(self, lot_id: int) -> Lot | None:
        """Атомарно переводит лот из «в продаже» в «забронирован» одним
        UPDATE с условием в WHERE. В отличие от «прочитать → проверить →
        записать» под блокировкой строки, не зависит от того, поддерживает
        ли конкретная СУБД блокировку (SELECT ... FOR UPDATE — no-op на
        SQLite) — гонка двойной брони закрыта на уровне одного атомарного
        запроса и на Postgres, и на SQLite. Возвращает None, если лот не
        найден или уже не в продаже (кто-то забронировал раньше)."""
        result = await self._session.execute(
            update(Lot)
            .where(Lot.id == lot_id, Lot.status == LotStatus.IN_SALE)
            .values(status=LotStatus.BOOKED)
            .returning(Lot)
        )
        return result.scalar_one_or_none()

    async def paginate(
        self, set_id: int, filters: LotFilters
    ) -> tuple[list[Lot], int]:
        query = select(Lot).where(Lot.set_id == set_id)

        if filters.project is not None:
            query = query.where(Lot.project == filters.project)
        if filters.rooms:
            query = query.where(Lot.rooms.in_(filters.rooms))
        if filters.status is not None:
            query = query.where(Lot.status == filters.status)
        if filters.price_m2_min is not None:
            query = query.where(Lot.price_per_m2 >= filters.price_m2_min)
        if filters.price_m2_max is not None:
            query = query.where(Lot.price_per_m2 <= filters.price_m2_max)

        total = await self._session.scalar(
            select(func.count()).select_from(query.subquery())
        )

        sort_col = _SORT_COLUMNS[filters.sort]
        ordering = sort_col.desc() if filters.order == SortOrder.DESC else sort_col.asc()
        query = query.order_by(ordering, Lot.id).offset(filters.offset).limit(filters.page_size)

        items = (await self._session.execute(query)).scalars().all()
        return list(items), total or 0

    async def distinct_projects(self, set_id: int) -> list[str]:
        result = await self._session.execute(
            select(Lot.project).where(Lot.set_id == set_id).distinct().order_by(Lot.project)
        )
        return list(result.scalars())

    async def bulk_insert(self, rows: list[dict[str, Any]]) -> None:
        if rows:
            await self._session.execute(insert(Lot), rows)
