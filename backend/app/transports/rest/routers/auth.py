from fastapi import APIRouter, Response

from app.schemas.auth import LoginParams, UserOut
from app.transports.deps import AdminDep, AuthDep, clear_session_cookie, set_session_cookie

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(data: LoginParams, response: Response, auth: AuthDep) -> UserOut:
    token = auth.login(data.login, data.password)
    set_session_cookie(response, token)
    return UserOut(login=data.login)


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    clear_session_cookie(response)


@router.get("/me")
async def me(admin: AdminDep) -> UserOut:
    return UserOut(login=admin)
