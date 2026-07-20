from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.common import Page
from app.schemas.request import RequestCreate, RequestFilters, RequestOut, RequestStatusUpdate
from app.services.requests import RequestService
from app.transports.deps import SessionDep, require_admin

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", status_code=201)
async def create_request(data: RequestCreate, session: SessionDep) -> RequestOut:
    return await RequestService(session).create(data)


@router.get("", dependencies=[Depends(require_admin)])
async def list_requests(
    session: SessionDep, filters: Annotated[RequestFilters, Query()]
) -> Page[RequestOut]:
    return await RequestService(session).list(filters)


@router.patch("/{request_id}", dependencies=[Depends(require_admin)])
async def set_request_status(
    request_id: int, data: RequestStatusUpdate, session: SessionDep
) -> RequestOut:
    return await RequestService(session).set_status(request_id, data.status)
