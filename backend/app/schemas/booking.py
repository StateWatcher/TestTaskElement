from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import BookingStatus
from app.schemas.common import ApiModel, PageParams
from app.schemas.lot import LotOut


class BookingCreate(BaseModel):
    lot_id: int
    name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=3, max_length=200, description="Телефон или почта")


class BookingFilters(PageParams):
    status: BookingStatus | None = None


class BookingOut(ApiModel):
    id: int
    lot_id: int
    name: str
    contact: str
    status: BookingStatus
    created_at: datetime
    lot: LotOut | None = None
