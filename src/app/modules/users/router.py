import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, require_permissions
from app.core.pagination import Page, Pagination
from app.db.session import SessionDep
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate, UserUpdateSelf
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


# ---- self ----
@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_me(session: SessionDep, user: CurrentUser, data: UserUpdateSelf) -> UserRead:
    return UserRead.model_validate(await UserService(session).update(user.id, data))


# ---- admin ----
@router.get("", response_model=Page[UserRead], dependencies=[require_permissions("users:read")])
async def list_users(session: SessionDep, params: Pagination) -> Page[UserRead]:
    page = await UserService(session).list(params)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permissions("users:write")],
)
async def create_user(session: SessionDep, data: UserCreate) -> UserRead:
    return UserRead.model_validate(await UserService(session).create(data))


@router.get("/{user_id}", response_model=UserRead, dependencies=[require_permissions("users:read")])
async def get_user(session: SessionDep, user_id: uuid.UUID) -> UserRead:
    return UserRead.model_validate(await UserService(session).get(user_id))


@router.patch(
    "/{user_id}", response_model=UserRead, dependencies=[require_permissions("users:write")]
)
async def update_user(session: SessionDep, user_id: uuid.UUID, data: UserUpdate) -> UserRead:
    return UserRead.model_validate(await UserService(session).update(user_id, data))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_permissions("users:write")],
)
async def delete_user(session: SessionDep, user_id: uuid.UUID) -> None:
    await UserService(session).delete(user_id)


@router.post(
    "/{user_id}/roles/{role_id}",
    response_model=UserRead,
    dependencies=[require_permissions("users:write", "roles:read")],
)
async def assign_role(session: SessionDep, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRead:
    return UserRead.model_validate(await UserService(session).assign_role(user_id, role_id))


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserRead,
    dependencies=[require_permissions("users:write", "roles:read")],
)
async def revoke_role(session: SessionDep, user_id: uuid.UUID, role_id: uuid.UUID) -> UserRead:
    return UserRead.model_validate(await UserService(session).revoke_role(user_id, role_id))
