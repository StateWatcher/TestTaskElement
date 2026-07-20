from pydantic import BaseModel

from app.schemas.common import ApiModel


class LoginParams(BaseModel):
    login: str
    password: str


class UserOut(ApiModel):
    login: str
