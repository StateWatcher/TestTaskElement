"""Сборка приложения: оба транспорта, CORS, обработчики доменных ошибок."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.db.session import get_engine
from app.domain.errors import (
    ConflictError,
    DomainError,
    FeedParseError,
    NotFoundError,
    Unauthorized,
)
from app.models import Base
from app.transports.jsonrpc import methods  # noqa: F401 — регистрация методов
from app.transports.jsonrpc.dispatcher import router as jsonrpc_router
from app.transports.rest.routers import router as rest_router

logger = logging.getLogger(__name__)

_ERROR_STATUS: list[tuple[type[DomainError], int]] = [
    (Unauthorized, 401),
    (NotFoundError, 404),
    (ConflictError, 409),
    (FeedParseError, 422),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    async with engine.begin() as conn:
        # осознанное упрощение вместо Alembic: одна версия схемы
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database ready")
    yield
    await engine.dispose()


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = next((code for cls, code in _ERROR_STATUS if isinstance(exc, cls)), 400)
    return JSONResponse(
        status_code=status,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app.log_level)

    app = FastAPI(title=settings.app.name, debug=settings.app.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(DomainError, domain_error_handler)

    app.include_router(rest_router, prefix=settings.app.api_prefix)
    app.include_router(jsonrpc_router, prefix=settings.app.api_prefix)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
