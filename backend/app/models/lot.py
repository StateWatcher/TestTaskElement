from datetime import datetime
from decimal import Decimal

from sqlalchemy import ColumnElement, ForeignKey, Index, Numeric, String, cast, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import LotStatus
from app.models.base import Base, now_utc


class Lot(Base):
    __tablename__ = "lots"
    __table_args__ = (
        Index("ix_lots_set_id_external_id", "set_id", "external_id", unique=True),
        Index("ix_lots_set_id_status", "set_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(64))
    set_id: Mapped[int] = mapped_column(ForeignKey("lot_sets.id", ondelete="CASCADE"))

    project: Mapped[str] = mapped_column()  # название жилого комплекса (ЖК)
    address: Mapped[str] = mapped_column()
    rooms: Mapped[int] = mapped_column()  # 0 = студия
    area: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    floor: Mapped[int] = mapped_column()
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    price_base: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[LotStatus] = mapped_column(String(16))

    created_at: Mapped[datetime] = mapped_column(default=now_utc, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=now_utc, onupdate=now_utc, server_default=func.now()
    )

    # единственное место, где определена формула цены за м²: работает и как
    # Python-свойство (lot.price_per_m2), и как SQL-выражение (Lot.price_per_m2
    # в фильтре/сортировке репозитория) — см. repositories/lots.py
    @hybrid_property
    def price_per_m2(self) -> Decimal | None:
        if not self.area:
            return None
        return round(self.price / self.area, 2)

    @price_per_m2.inplace.expression
    @classmethod
    def _price_per_m2_expression(cls) -> ColumnElement:
        return cast(cls.price / func.nullif(cls.area, 0), Numeric(14, 2))
