"""Доменные статусы. Живут отдельно от ORM, чтобы схемы и сервисы
не тянули зависимость на слой персистентности."""

from enum import StrEnum


class LotStatus(StrEnum):
    IN_SALE = "in_sale"
    BOOKED = "booked"
    SOLD = "sold"


class BookingStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class RequestStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
