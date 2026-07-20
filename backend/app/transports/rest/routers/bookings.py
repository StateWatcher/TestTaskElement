from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.booking import BookingCreate, BookingFilters, BookingOut
from app.schemas.common import Page
from app.services.booking import BookingService
from app.transports.deps import SessionDep, require_admin

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", status_code=201)
async def create_booking(data: BookingCreate, session: SessionDep) -> BookingOut:
    return await BookingService(session).create(data)


@router.get("", dependencies=[Depends(require_admin)])
async def list_bookings(
    session: SessionDep, filters: Annotated[BookingFilters, Query()]
) -> Page[BookingOut]:
    return await BookingService(session).list(filters)


@router.post("/{booking_id}/cancel", dependencies=[Depends(require_admin)])
async def cancel_booking(booking_id: int, session: SessionDep) -> BookingOut:
    return await BookingService(session).cancel(booking_id)
