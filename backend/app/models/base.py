from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    # timestamptz вместо naive timestamp; python-side default, чтобы значение
    # было известно сразу после flush и не требовало дозагрузки в async-коде
    type_annotation_map = {datetime: DateTime(timezone=True)}


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(default=now_utc, server_default=func.now())
