"""JSON-RPC 2.0 поверх одного POST-эндпоинта.

Метод — асинхронная функция ``handler(ctx, params)``; params валидируются
pydantic-моделью, доменные ошибки транслируются в коды JSON-RPC. Тело
разбирается вручную, чтобы отвечать ошибками протокола (-32700/-32600),
а не HTTP 422. Ответ всегда HTTP 200 — семантика ошибок живёт в payload.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import (
    ConflictError,
    DomainError,
    FeedParseError,
    NotFoundError,
    Unauthorized,
)
from app.transports.deps import AuthDep, SessionDep, session_login

logger = logging.getLogger(__name__)

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR = -32000
UNAUTHORIZED = -32001
NOT_FOUND = -32002
CONFLICT = -32003
UNPROCESSABLE = -32004

_DOMAIN_CODES: list[tuple[type[DomainError], int]] = [
    (Unauthorized, UNAUTHORIZED),
    (NotFoundError, NOT_FOUND),
    (ConflictError, CONFLICT),
    (FeedParseError, UNPROCESSABLE),
]


@dataclass
class RpcContext:
    session: AsyncSession
    response: Response
    admin: str | None  # логин, если запрос пришёл с валидной сессией


Handler = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class Method:
    handler: Handler
    params_model: type[BaseModel] | None
    requires_auth: bool


_METHODS: dict[str, Method] = {}


def method(name: str, params_model: type[BaseModel] | None = None, requires_auth: bool = False):
    def decorator(handler: Handler) -> Handler:
        if name in _METHODS:
            raise ValueError(f"JSON-RPC method already registered: {name}")
        _METHODS[name] = Method(handler, params_model, requires_auth)
        return handler

    return decorator


def method_names() -> list[str]:
    return sorted(_METHODS)


class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: dict[str, Any] | None = None
    id: str | int | None = None


def _error(
    code: int, message: str, request_id: str | int | None, data: Any = None
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "error": error, "id": request_id}


def _serialize(result: Any) -> Any:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    if isinstance(result, list):
        return [_serialize(item) for item in result]
    return result


router = APIRouter(prefix="/jsonrpc", tags=["jsonrpc"])


@router.post("")
async def handle(
    request: Request, response: Response, session: SessionDep, auth: AuthDep
) -> dict[str, Any]:
    try:
        body = await request.json()
    except ValueError:
        return _error(PARSE_ERROR, "Parse error", None)
    try:
        rpc = JsonRpcRequest.model_validate(body)
    except ValidationError:
        return _error(INVALID_REQUEST, "Invalid request", _request_id(body))
    if rpc.jsonrpc != "2.0":
        return _error(INVALID_REQUEST, "jsonrpc must be '2.0'", rpc.id)

    registered = _METHODS.get(rpc.method)
    if registered is None:
        return _error(METHOD_NOT_FOUND, f"Unknown method: {rpc.method}", rpc.id)

    admin = session_login(request, auth)
    if registered.requires_auth and admin is None:
        return _error(UNAUTHORIZED, "Unauthorized", rpc.id)

    ctx = RpcContext(session=session, response=response, admin=admin)
    try:
        if registered.params_model is None:
            result = await registered.handler(ctx)
        else:
            params = registered.params_model.model_validate(rpc.params or {})
            result = await registered.handler(ctx, params)
    except ValidationError as exc:
        return _error(INVALID_PARAMS, "Invalid params", rpc.id, data=exc.errors())
    except DomainError as exc:
        code = next((c for cls, c in _DOMAIN_CODES if isinstance(exc, cls)), SERVER_ERROR)
        return _error(code, exc.message, rpc.id, data={"code": exc.code})
    except Exception:
        logger.exception("jsonrpc method failed", extra={"method": rpc.method})
        return _error(INTERNAL_ERROR, "Internal error", rpc.id)

    return {"jsonrpc": "2.0", "result": _serialize(result), "id": rpc.id}


def _request_id(body: Any) -> str | int | None:
    if isinstance(body, dict) and isinstance(body.get("id"), str | int):
        return body["id"]
    return None
