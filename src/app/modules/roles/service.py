import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.db.repository import Repository
from app.modules.roles.models import Role
from app.modules.roles.schemas import RoleCreate, RoleUpdate

# Seeded by `python -m app.cli seed`. Extend freely; permissions are plain strings.
DEFAULT_ROLES: dict[str, dict[str, object]] = {
    "admin": {"description": "Full access", "permissions": ["*"]},
    "user": {
        "description": "Standard user",
        "permissions": ["users:read_self", "users:write_self", "ai:invoke"],
    },
}


class RoleRepository(Repository[Role]):
    model = Role


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = RoleRepository(session)

    async def get(self, role_id: uuid.UUID) -> Role:
        role = await self.repo.get(role_id)
        if role is None:
            raise NotFoundError("Role not found")
        return role

    async def get_by_name(self, name: str) -> Role | None:
        return await self.repo.get_by(name=name)

    async def list(self, params: PageParams) -> Page[Role]:
        return await self.repo.list(params, self.repo.query().order_by(Role.name))

    async def create(self, data: RoleCreate) -> Role:
        if await self.repo.exists(name=data.name):
            raise ConflictError(f"Role '{data.name}' already exists")
        return await self.repo.create(**data.model_dump())

    async def update(self, role_id: uuid.UUID, data: RoleUpdate) -> Role:
        role = await self.get(role_id)
        return await self.repo.update(role, **data.model_dump(exclude_unset=True))

    async def delete(self, role_id: uuid.UUID) -> None:
        await self.repo.delete(await self.get(role_id))

    async def ensure_defaults(self) -> None:
        for name, spec in DEFAULT_ROLES.items():
            if not await self.repo.exists(name=name):
                await self.repo.create(name=name, **spec)
