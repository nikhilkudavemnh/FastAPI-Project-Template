import uuid

from fastapi import APIRouter, status

from app.api.deps import require_permissions
from app.core.pagination import Page, Pagination
from app.db.session import SessionDep
from app.modules.roles.schemas import RoleCreate, RoleRead, RoleUpdate
from app.modules.roles.service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=Page[RoleRead], dependencies=[require_permissions("roles:read")])
async def list_roles(session: SessionDep, params: Pagination) -> Page[RoleRead]:
    page = await RoleService(session).list(params)
    return Page[RoleRead](
        items=[RoleRead.model_validate(r) for r in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permissions("roles:write")],
)
async def create_role(session: SessionDep, data: RoleCreate) -> RoleRead:
    return RoleRead.model_validate(await RoleService(session).create(data))


@router.get("/{role_id}", response_model=RoleRead, dependencies=[require_permissions("roles:read")])
async def get_role(session: SessionDep, role_id: uuid.UUID) -> RoleRead:
    return RoleRead.model_validate(await RoleService(session).get(role_id))


@router.patch(
    "/{role_id}", response_model=RoleRead, dependencies=[require_permissions("roles:write")]
)
async def update_role(session: SessionDep, role_id: uuid.UUID, data: RoleUpdate) -> RoleRead:
    return RoleRead.model_validate(await RoleService(session).update(role_id, data))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_permissions("roles:write")],
)
async def delete_role(session: SessionDep, role_id: uuid.UUID) -> None:
    await RoleService(session).delete(role_id)
