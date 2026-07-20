from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile

from app.schemas.common import Page, PageParams
from app.schemas.lot_set import FeedUploadResult, LotSetOut
from app.services.feed import FeedService
from app.transports.deps import SessionDep, require_admin

router = APIRouter(prefix="/sets", tags=["sets"], dependencies=[Depends(require_admin)])


@router.post("", status_code=201)
async def upload_feed(file: UploadFile, session: SessionDep) -> FeedUploadResult:
    content = await file.read()
    return await FeedService(session).import_feed(file.filename or "feed.xml", content)


@router.get("")
async def list_sets(
    session: SessionDep, filters: Annotated[PageParams, Query()]
) -> Page[LotSetOut]:
    return await FeedService(session).list_sets(filters)


@router.post("/{set_id}/activate")
async def activate_set(set_id: int, session: SessionDep) -> LotSetOut:
    return await FeedService(session).activate_set(set_id)
