"""Зависимости, общие для обоих транспортов: сессия БД и cookie-авторизация."""

from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.session import get_session
from app.domain.errors import Unauthorized
from app.services.auth import AuthService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service() -> AuthService:
    return AuthService(get_settings().auth)


AuthDep = Annotated[AuthService, Depends(get_auth_service)]


def session_login(request: Request, auth: AuthService) -> str | None:
    return auth.verify(request.cookies.get(get_settings().auth.cookie_name))


def require_admin(request: Request, auth: AuthDep) -> str:
    login = session_login(request, auth)
    if login is None:
        raise Unauthorized
    return login


AdminDep = Annotated[str, Depends(require_admin)]


def set_session_cookie(response: Response, token: str) -> None:
    auth = get_settings().auth
    response.set_cookie(
        auth.cookie_name,
        token,
        max_age=auth.session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=auth.cookie_secure,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(get_settings().auth.cookie_name)
