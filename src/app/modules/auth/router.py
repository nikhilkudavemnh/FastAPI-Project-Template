from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, SettingsDep
from app.db.session import SessionDep
from app.modules.auth.schemas import RefreshRequest, RegisterRequest, TokenPair
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(session: SessionDep, settings: SettingsDep, data: RegisterRequest) -> UserRead:
    return UserRead.model_validate(await AuthService(session, settings).register(data))


@router.post("/login", response_model=TokenPair)
async def login(
    session: SessionDep,
    settings: SettingsDep,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenPair:
    svc = AuthService(session, settings)
    user = await svc.authenticate(form.username, form.password)
    return svc.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(session: SessionDep, settings: SettingsDep, data: RefreshRequest) -> TokenPair:
    return await AuthService(session, settings).refresh(data.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
