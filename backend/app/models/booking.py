from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import BookingStatus
from app.models.base import Base, CreatedAtMixin
from app.models.lot import Lot


class Booking(Base, CreatedAtMixin):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column()
    contact: Mapped[str] = mapped_column()  # телефон или почта
    status: Mapped[BookingStatus] = mapped_column(String(16), default=BookingStatus.ACTIVE)

    lot: Mapped[Lot] = relationship(lazy="selectin")
