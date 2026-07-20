from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LotSet
from app.schemas.common import PageParams


class LotSetRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, name: str) -> LotSet:
        lot_set = LotSet(name=name)
        self._session.add(lot_set)
        await self._session.flush()
        return lot_set

    async def get(self, set_id: int) -> LotSet | None:
        return await self._session.get(LotSet, set_id)

    async def get_active(self) -> LotSet | None:
        result = await self._session.execute(select(LotSet).where(LotSet.is_active))
        return result.scalar_one_or_none()

    async def paginate(self, filters: PageParams) -> tuple[list[LotSet], int]:
        query = select(LotSet)
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        query = (
            query.order_by(LotSet.uploaded_at.desc(), LotSet.id.desc())
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        items = (await self._session.execute(query)).scalars().all()
        return list(items), total or 0

    async def set_active(self, set_id: int) -> None:
        """Активным может быть только один набор."""
        await self._session.execute(update(LotSet).values(is_active=(LotSet.id == set_id)))
