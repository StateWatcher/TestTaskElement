"""Доменные ошибки. Транспорты сами решают, как их отдавать наружу:
REST — HTTP-статусами, JSON-RPC — кодами ошибок."""


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.__doc__ or self.code
        super().__init__(self.message)


class NotFoundError(DomainError):
    code = "not_found"


class LotNotFound(NotFoundError):
    """Лот не найден."""

    code = "lot_not_found"


class SetNotFound(NotFoundError):
    """Набор лотов не найден."""

    code = "set_not_found"


class BookingNotFound(NotFoundError):
    """Бронь не найдена."""

    code = "booking_not_found"


class RequestNotFound(NotFoundError):
    """Заявка не найдена."""

    code = "request_not_found"


class ConflictError(DomainError):
    code = "conflict"


class LotNotAvailable(ConflictError):
    """Лот недоступен для брони."""

    code = "lot_not_available"


class Unauthorized(DomainError):
    """Требуется авторизация."""

    code = "unauthorized"


class InvalidCredentials(Unauthorized):
    """Неверный логин или пароль."""

    code = "invalid_credentials"


class FeedParseError(DomainError):
    """Не удалось разобрать фид."""

    code = "feed_parse_error"
