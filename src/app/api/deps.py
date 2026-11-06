"""Reusable FastAPI dependencies: settings, current user, role/permission guards."""

import uuid
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import SessionDep
from app.modules.users.models import User
from app.modules.users.service import UserService

SettingsDep = Annotated[Settings, Depends(get_settings)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise UnauthorizedError("Not authenticated")
    payload = decode_token(settings, token, expected_type="access")
    user = await UserService(session).repo.get(uuid.UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permissions(*permissions: str) -> Any:
    """Use as a route/router dependency: dependencies=[require_permissions("users:read")]."""

    async def _check(user: CurrentUser) -> User:
        missing = [p for p in permissions if not user.has_permission(p)]
        if missing:
            raise ForbiddenError(f"Missing permissions: {', '.join(missing)}")
        return user

    return Depends(_check)


def require_roles(*roles: str) -> Any:
    async def _check(user: CurrentUser) -> User:
        if not any(user.has_role(r) for r in roles):
            raise ForbiddenError(f"Requires one of roles: {', '.join(roles)}")
        return user

    return Depends(_check)


def require_superuser() -> Any:
    async def _check(user: CurrentUser) -> User:
        if not user.is_superuser:
            raise ForbiddenError("Superuser required")
        return user

    return Depends(_check)
