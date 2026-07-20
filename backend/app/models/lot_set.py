from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, now_utc


class LotSet(Base):
    __tablename__ = "lot_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()  # имя исходного файла фида
    uploaded_at: Mapped[datetime] = mapped_column(default=now_utc, server_default=func.now())
    lots_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=False)
