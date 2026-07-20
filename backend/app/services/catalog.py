"""Публичная витрина: лоты активного набора с фильтрами, сортировкой, пагинацией."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import LotNotFound
from app.repositories.lot_sets import LotSetRepository
from app.repositories.lots import LotRepository
from app.schemas.common import Page
from app.schemas.lot import LotFilters, LotOut


class CatalogService:
    def __init__(self, session: AsyncSession):
        self._lots = LotRepository(session)
        self._sets = LotSetRepository(session)

    async def list_lots(self, filters: LotFilters) -> Page[LotOut]:
        active = await self._sets.get_active()
        if active is None:
            return Page(items=[], total=0, page=filters.page, page_size=filters.page_size)
        items, total = await self._lots.paginate(active.id, filters)
        return Page(
            items=[LotOut.model_validate(lot) for lot in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def get_lot(self, lot_id: int) -> LotOut:
        """Публично виден только лот активного набора."""
        active = await self._sets.get_active()
        lot = await self._lots.get(lot_id)
        if lot is None or active is None or lot.set_id != active.id:
            raise LotNotFound
        return LotOut.model_validate(lot)

    async def projects(self) -> list[str]:
        active = await self._sets.get_active()
        if active is None:
            return []
        return await self._lots.distinct_projects(active.id)
