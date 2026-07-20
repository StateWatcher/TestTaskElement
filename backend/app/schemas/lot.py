from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from app.domain.enums import LotStatus
from app.schemas.common import ApiModel, PageParams


class LotSortField(StrEnum):
    PRICE = "price"
    PRICE_PER_M2 = "price_per_m2"
    AREA = "area"
    FLOOR = "floor"
    ROOMS = "rooms"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class LotFilters(PageParams):
    project: str | None = None
    rooms: list[int] | None = Field(None, description="Комнатность, 0 — студия")
    price_m2_min: Decimal | None = Field(None, ge=0)
    price_m2_max: Decimal | None = Field(None, ge=0)
    status: LotStatus | None = None
    sort: LotSortField = LotSortField.PRICE
    order: SortOrder = SortOrder.ASC


class LotOut(ApiModel):
    id: int
    external_id: str
    set_id: int
    project: str
    address: str
    rooms: int
    area: Decimal
    floor: int
    price: Decimal
    price_base: Decimal
    status: LotStatus
    price_per_m2: Decimal | None  # значение — hybrid_property Lot.price_per_m2
    created_at: datetime
    updated_at: datetime
