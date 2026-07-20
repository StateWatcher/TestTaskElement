"""Привязка JSON-RPC методов к сервисам. Логика — в services/, здесь только клей транспорта.

Загрузка фида через JSON-RPC принимает base64 — у протокола нет multipart,
это осознанный компромисс ради паритета транспортов.
"""

import base64
import binascii

from pydantic import BaseModel

from app.domain.enums import RequestStatus
from app.domain.errors import FeedParseError
from app.schemas.auth import LoginParams, UserOut
from app.schemas.booking import BookingCreate, BookingFilters
from app.schemas.common import PageParams
from app.schemas.lot import LotFilters
from app.schemas.request import RequestCreate, RequestFilters
from app.services.booking import BookingService
from app.services.catalog import CatalogService
from app.services.feed import FeedService
from app.services.requests import RequestService
from app.transports.deps import clear_session_cookie, get_auth_service, set_session_cookie
from app.transports.jsonrpc.dispatcher import RpcContext, method


class LotGetParams(BaseModel):
    lot_id: int


class BookingCancelParams(BaseModel):
    booking_id: int


class RequestSetStatusParams(BaseModel):
    request_id: int
    status: RequestStatus


class SetActivateParams(BaseModel):
    set_id: int


class FeedUploadParams(BaseModel):
    filename: str
    content_base64: str


@method("lots.list", LotFilters)
async def lots_list(ctx: RpcContext, params: LotFilters):
    return await CatalogService(ctx.session).list_lots(params)


@method("lots.get", LotGetParams)
async def lots_get(ctx: RpcContext, params: LotGetParams):
    return await CatalogService(ctx.session).get_lot(params.lot_id)


@method("lots.projects")
async def lots_projects(ctx: RpcContext):
    return await CatalogService(ctx.session).projects()


@method("bookings.create", BookingCreate)
async def bookings_create(ctx: RpcContext, params: BookingCreate):
    return await BookingService(ctx.session).create(params)


@method("requests.create", RequestCreate)
async def requests_create(ctx: RpcContext, params: RequestCreate):
    return await RequestService(ctx.session).create(params)


@method("auth.login", LoginParams)
async def auth_login(ctx: RpcContext, params: LoginParams):
    token = get_auth_service().login(params.login, params.password)
    set_session_cookie(ctx.response, token)
    return UserOut(login=params.login)


@method("auth.logout")
async def auth_logout(ctx: RpcContext):
    clear_session_cookie(ctx.response)
    return True


@method("auth.me", requires_auth=True)
async def auth_me(ctx: RpcContext):
    return UserOut(login=ctx.admin or "")


@method("admin.sets.upload", FeedUploadParams, requires_auth=True)
async def sets_upload(ctx: RpcContext, params: FeedUploadParams):
    try:
        content = base64.b64decode(params.content_base64, validate=True)
    except binascii.Error as exc:
        raise FeedParseError("content_base64 не является корректным base64") from exc
    return await FeedService(ctx.session).import_feed(params.filename, content)


@method("admin.sets.list", PageParams, requires_auth=True)
async def sets_list(ctx: RpcContext, params: PageParams):
    return await FeedService(ctx.session).list_sets(params)


@method("admin.sets.activate", SetActivateParams, requires_auth=True)
async def sets_activate(ctx: RpcContext, params: SetActivateParams):
    return await FeedService(ctx.session).activate_set(params.set_id)


@method("admin.bookings.list", BookingFilters, requires_auth=True)
async def bookings_list(ctx: RpcContext, params: BookingFilters):
    return await BookingService(ctx.session).list(params)


@method("admin.bookings.cancel", BookingCancelParams, requires_auth=True)
async def bookings_cancel(ctx: RpcContext, params: BookingCancelParams):
    return await BookingService(ctx.session).cancel(params.booking_id)


@method("admin.requests.list", RequestFilters, requires_auth=True)
async def requests_list(ctx: RpcContext, params: RequestFilters):
    return await RequestService(ctx.session).list(params)


@method("admin.requests.set_status", RequestSetStatusParams, requires_auth=True)
async def requests_set_status(ctx: RpcContext, params: RequestSetStatusParams):
    return await RequestService(ctx.session).set_status(params.request_id, params.status)
