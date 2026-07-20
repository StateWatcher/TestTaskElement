from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import RequestStatus
from app.schemas.common import ApiModel, PageParams
from app.schemas.lot import LotOut


class RequestCreate(BaseModel):
    lot_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    contact: str = Field(min_length=3, max_length=200, description="Телефон или почта")
    comment: str = Field(min_length=1, max_length=5000)


class RequestFilters(PageParams):
    status: RequestStatus | None = None


class RequestStatusUpdate(BaseModel):
    status: RequestStatus


class RequestOut(ApiModel):
    id: int
    lot_id: int | None
    name: str
    contact: str
    comment: str
    status: RequestStatus
    created_at: datetime
    lot: LotOut | None = None
