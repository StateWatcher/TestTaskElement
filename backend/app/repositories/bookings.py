from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking
from app.schemas.booking import BookingFilters


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def add(self, booking: Booking) -> None:
        self._session.add(booking)

    async def get(self, booking_id: int) -> Booking | None:
        return await self._session.get(Booking, booking_id)

    async def paginate(self, filters: BookingFilters) -> tuple[list[Booking], int]:
        query = select(Booking)
        if filters.status is not None:
            query = query.where(Booking.status == filters.status)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        query = (
            query.order_by(Booking.created_at.desc(), Booking.id.desc())
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        items = (await self._session.execute(query)).scalars().all()
        return list(items), total or 0
