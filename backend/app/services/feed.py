"""Разбор XML-фида и создание набора лотов.

Структура фида: feed > object (ЖК) > buildings > building > flats > flat.
Модель сервиса плоская: лот = квартира с привязкой к ЖК и адресу.
Некорректные лоты пропускаются и подсчитываются, а не валят импорт целиком.
"""

import logging
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import LotStatus
from app.domain.errors import FeedParseError, SetNotFound
from app.repositories.lot_sets import LotSetRepository
from app.repositories.lots import LotRepository
from app.schemas.common import Page, PageParams
from app.schemas.lot_set import FeedUploadResult, LotSetOut

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    "FREE": LotStatus.IN_SALE,
    "RESERVED": LotStatus.BOOKED,
    "SOLD": LotStatus.SOLD,
}


def _text(node: ET.Element, path: str) -> str | None:
    child = node.find(path)
    if child is None or child.text is None:
        return None
    return child.text.strip() or None


def parse_feed(content: bytes) -> tuple[list[dict[str, Any]], int]:
    """Возвращает (строки для вставки без set_id, количество пропущенных)."""
    # реальный фид начинается с мусорного префикса ("//<?xml ...") — срезаем всё до первого "<"
    start = content.find(b"<")
    if start == -1:
        raise FeedParseError("В файле нет XML")
    try:
        root = ET.fromstring(content[start:])
    except ET.ParseError as exc:
        raise FeedParseError(f"Некорректный XML: {exc}") from exc
    if root.tag != "feed":
        raise FeedParseError("Ожидался корневой элемент <feed>")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    skipped = 0
    for obj in root.iterfind("object"):
        project = _text(obj, "name")
        obj_address = _text(obj, "address")
        if project is None:
            continue
        for building in obj.iterfind("buildings/building"):
            address = _text(building, "address") or obj_address or ""
            for flat in building.iterfind("flats/flat"):
                row = _parse_flat(flat, project, address)
                if row is None or row["external_id"] in seen:
                    skipped += 1
                    continue
                seen.add(row["external_id"])
                rows.append(row)
    return rows, skipped


def _parse_flat(flat: ET.Element, project: str, address: str) -> dict[str, Any] | None:
    external_id = _text(flat, "flat_id")
    status = _STATUS_MAP.get(_text(flat, "status") or "")
    if external_id is None or status is None:
        return None
    try:
        return {
            "external_id": external_id,
            "project": project,
            "address": address,
            "rooms": int(_text(flat, "room") or ""),
            "area": Decimal(_text(flat, "area") or ""),
            "floor": int(_text(flat, "floor") or ""),
            "price": Decimal(_text(flat, "price") or ""),
            "price_base": Decimal(_text(flat, "price_base") or ""),
            "status": status,
        }
    except (ValueError, InvalidOperation):
        return None


class FeedService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._sets = LotSetRepository(session)
        self._lots = LotRepository(session)

    async def import_feed(self, filename: str, content: bytes) -> FeedUploadResult:
        rows, skipped = parse_feed(content)
        if not rows:
            raise FeedParseError("В фиде не нашлось ни одного корректного лота")

        lot_set = await self._sets.create(name=filename)
        for row in rows:
            row["set_id"] = lot_set.id
        await self._lots.bulk_insert(rows)
        lot_set.lots_count = len(rows)
        await self._session.commit()

        logger.info(
            "feed imported",
            extra={"set_id": lot_set.id, "lots": len(rows), "skipped": skipped},
        )
        return FeedUploadResult(set=LotSetOut.model_validate(lot_set), skipped=skipped)

    async def list_sets(self, filters: PageParams) -> Page[LotSetOut]:
        items, total = await self._sets.paginate(filters)
        return Page(
            items=[LotSetOut.model_validate(s) for s in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def activate_set(self, set_id: int) -> LotSetOut:
        lot_set = await self._sets.get(set_id)
        if lot_set is None:
            raise SetNotFound
        await self._sets.set_active(set_id)
        await self._session.commit()
        await self._session.refresh(lot_set)
        logger.info("set activated", extra={"set_id": set_id})
        return LotSetOut.model_validate(lot_set)
