"""Заявки: публичная форма без обязательной привязки к лоту, статусы новая → в работе → закрыта."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import RequestStatus
from app.domain.errors import LotNotFound, RequestNotFound
from app.models import Request
from app.repositories.lots import LotRepository
from app.repositories.requests import RequestRepository
from app.schemas.common import Page
from app.schemas.request import RequestCreate, RequestFilters, RequestOut

logger = logging.getLogger(__name__)


class RequestService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._requests = RequestRepository(session)
        self._lots = LotRepository(session)

    async def create(self, data: RequestCreate) -> RequestOut:
        lot = None
        if data.lot_id is not None:
            lot = await self._lots.get(data.lot_id)
            if lot is None:
                raise LotNotFound
        request = Request(lot=lot, name=data.name, contact=data.contact, comment=data.comment)
        self._requests.add(request)
        await self._session.commit()
        logger.info("request created", extra={"request_id": request.id, "lot_id": data.lot_id})
        return RequestOut.model_validate(request)

    async def set_status(self, request_id: int, status: RequestStatus) -> RequestOut:
        request = await self._requests.get(request_id)
        if request is None:
            raise RequestNotFound
        request.status = status
        await self._session.commit()
        logger.info("request status changed", extra={"request_id": request.id, "status": status})
        return RequestOut.model_validate(request)

    async def list(self, filters: RequestFilters) -> Page[RequestOut]:
        items, total = await self._requests.paginate(filters)
        return Page(
            items=[RequestOut.model_validate(r) for r in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )
