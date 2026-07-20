"""Правила брони и переходы статусов лота.

Бронируется только лот активного набора в статусе «в продаже»; лот при этом
переходит в «забронирован». Отмена брони возвращает лот в продажу и, в отличие
от брони, использует блокировку строки (LotRepository.get_for_update) — путь
редкий и без конкурентной нагрузки на клик. Защита от двойной брони — атомарный
UPDATE в LotRepository.try_book, механизм и обоснование описаны там.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BookingStatus, LotStatus
from app.domain.errors import BookingNotFound, LotNotAvailable, LotNotFound
from app.models import Booking
from app.repositories.bookings import BookingRepository
from app.repositories.lot_sets import LotSetRepository
from app.repositories.lots import LotRepository
from app.schemas.booking import BookingCreate, BookingFilters, BookingOut
from app.schemas.common import Page

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._bookings = BookingRepository(session)
        self._lots = LotRepository(session)
        self._sets = LotSetRepository(session)

    async def create(self, data: BookingCreate) -> BookingOut:
        lot = await self._lots.get(data.lot_id)
        if lot is None:
            raise LotNotFound
        active = await self._sets.get_active()
        if active is None or lot.set_id != active.id:
            raise LotNotFound

        booked_lot = await self._lots.try_book(data.lot_id)
        if booked_lot is None:
            raise LotNotAvailable

        # передаём уже загруженный Lot напрямую, а не lot_id: экономим лишний
        # selectin-запрос при сериализации booking.lot
        booking = Booking(lot=booked_lot, name=data.name, contact=data.contact)
        self._bookings.add(booking)
        await self._session.commit()

        logger.info("booking created", extra={"booking_id": booking.id, "lot_id": booked_lot.id})
        return BookingOut.model_validate(booking)

    async def cancel(self, booking_id: int) -> BookingOut:
        booking = await self._bookings.get(booking_id)
        if booking is None:
            raise BookingNotFound
        if booking.status == BookingStatus.ACTIVE:
            booking.status = BookingStatus.CANCELLED
            lot = await self._lots.get_for_update(booking.lot_id)
            if lot is not None and lot.status == LotStatus.BOOKED:
                lot.status = LotStatus.IN_SALE
            await self._session.commit()
            logger.info(
                "booking cancelled", extra={"booking_id": booking.id, "lot_id": booking.lot_id}
            )
        return BookingOut.model_validate(booking)

    async def list(self, filters: BookingFilters) -> Page[BookingOut]:
        items, total = await self._bookings.paginate(filters)
        return Page(
            items=[BookingOut.model_validate(b) for b in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )
