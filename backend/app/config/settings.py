"""Конфигурация приложения.

Разделение по группам с собственными env-префиксами:

- ``POSTGRES_*`` — подключение к БД; те же переменные использует контейнер
  postgres в docker-compose, поэтому значение (например, порт) задаётся
  ровно в одном месте — в ``.env``.
- ``AUTH_*``   — секреты авторизации (ключ подписи сессии, суперюзер).
- ``APP_*``    — технические параметры приложения, у всех есть дефолты.

Секреты дефолтов не имеют: без них приложение не стартует.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Group(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DatabaseSettings(_Group):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")

    host: str = "db"
    port: int = 5432
    user: str = "app"
    password: str
    db: str = "lots"

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class AuthSettings(_Group):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    secret_key: str
    superuser_login: str
    superuser_password: str
    session_ttl_seconds: int = 12 * 60 * 60
    cookie_name: str = "session"
    cookie_secure: bool = False


class AppSettings(_Group):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    name: str = "lot-selector"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


class Settings(BaseSettings):
    app: AppSettings
    db: DatabaseSettings
    auth: AuthSettings


@lru_cache
def get_settings() -> Settings:
    return Settings(app=AppSettings(), db=DatabaseSettings(), auth=AuthSettings())
