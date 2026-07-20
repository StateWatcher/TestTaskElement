from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import RequestStatus
from app.models.base import Base, CreatedAtMixin
from app.models.lot import Lot


class Request(Base, CreatedAtMixin):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column()
    contact: Mapped[str] = mapped_column()
    comment: Mapped[str] = mapped_column(Text)
    status: Mapped[RequestStatus] = mapped_column(String(16), default=RequestStatus.NEW)

    lot: Mapped[Lot | None] = relationship(lazy="selectin")
