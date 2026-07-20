from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.common import Page
from app.schemas.lot import LotFilters, LotOut
from app.services.catalog import CatalogService
from app.transports.deps import SessionDep

router = APIRouter(prefix="/lots", tags=["lots"])


@router.get("")
async def list_lots(session: SessionDep, filters: Annotated[LotFilters, Query()]) -> Page[LotOut]:
    return await CatalogService(session).list_lots(filters)


@router.get("/projects")
async def list_projects(session: SessionDep) -> list[str]:
    return await CatalogService(session).projects()


@router.get("/{lot_id}")
async def get_lot(lot_id: int, session: SessionDep) -> LotOut:
    return await CatalogService(session).get_lot(lot_id)
