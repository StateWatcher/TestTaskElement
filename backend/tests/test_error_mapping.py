"""Проверяет, что каждый подкласс DomainError отражён в обоих местах перевода
в наружные коды — app.main._ERROR_STATUS (REST) и
app.transports.jsonrpc.dispatcher._DOMAIN_CODES (JSON-RPC). Оба списка
обновляются вручную, и без этой проверки забытый в одном из них новый класс
ошибки тихо уходил бы в default-код вместо честного 404/409/etc."""

from app.domain.errors import DomainError
from app.main import _ERROR_STATUS
from app.transports.jsonrpc.dispatcher import _DOMAIN_CODES


def _all_domain_error_subclasses() -> set[type[DomainError]]:
    seen: set[type[DomainError]] = set()
    stack = [DomainError]
    while stack:
        for sub in stack.pop().__subclasses__():
            if sub not in seen:
                seen.add(sub)
                stack.append(sub)
    return seen


def test_every_domain_error_has_http_status():
    for cls in _all_domain_error_subclasses():
        assert any(issubclass(cls, base) for base, _ in _ERROR_STATUS), (
            f"{cls.__name__} не отражён в app.main._ERROR_STATUS"
        )


def test_every_domain_error_has_jsonrpc_code():
    for cls in _all_domain_error_subclasses():
        assert any(issubclass(cls, base) for base, _ in _DOMAIN_CODES), (
            f"{cls.__name__} не отражён в app.transports.jsonrpc.dispatcher._DOMAIN_CODES"
        )
