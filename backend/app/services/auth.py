"""Авторизация суперюзера: проверка пары логин/пароль из конфига
и подписанный токен сессии для HttpOnly-cookie."""

import logging
import secrets

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config.settings import AuthSettings
from app.domain.errors import InvalidCredentials

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, settings: AuthSettings):
        self._settings = settings
        self._serializer = URLSafeTimedSerializer(settings.secret_key, salt="admin-session")

    def login(self, login: str, password: str) -> str:
        """Возвращает токен сессии; при неверных кредах — InvalidCredentials."""
        login_ok = secrets.compare_digest(login, self._settings.superuser_login)
        password_ok = secrets.compare_digest(password, self._settings.superuser_password)
        if not (login_ok and password_ok):
            logger.info("login failed", extra={"login": login})
            raise InvalidCredentials
        logger.info("login ok", extra={"login": login})
        return self._serializer.dumps({"login": login})

    def verify(self, token: str | None) -> str | None:
        """Логин из валидного токена либо None."""
        if not token:
            return None
        try:
            data = self._serializer.loads(token, max_age=self._settings.session_ttl_seconds)
        except BadSignature:
            return None
        return data.get("login")
