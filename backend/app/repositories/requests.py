from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Request
from app.schemas.request import RequestFilters


class RequestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, request: Request) -> None:
        self._session.add(request)

    async def get(self, request_id: int) -> Request | None:
        return await self._session.get(Request, request_id)

    async def paginate(self, filters: RequestFilters) -> tuple[list[Request], int]:
        query = select(Request)
        if filters.status is not None:
            query = query.where(Request.status == filters.status)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        query = (
            query.order_by(Request.created_at.desc(), Request.id.desc())
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        items = (await self._session.execute(query)).scalars().all()
        return list(items), total or 0
