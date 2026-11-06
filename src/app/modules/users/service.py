import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import Page, PageParams
from app.core.security import hash_password
from app.db.repository import Repository
from app.modules.roles.service import RoleService
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate, UserUpdateSelf


class UserRepository(Repository[User]):
    model = User


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.roles = RoleService(session)

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by(email=email.lower())

    async def list(self, params: PageParams) -> Page[User]:
        return await self.repo.list(params, self.repo.query().order_by(User.created_at.desc()))

    async def create(self, data: UserCreate) -> User:
        email = data.email.lower()
        if await self.repo.exists(email=email):
            raise ConflictError("Email already registered")
        roles = []
        for name in data.role_names:
            role = await self.roles.get_by_name(name)
            if role is None:
                raise NotFoundError(f"Role '{name}' not found")
            roles.append(role)
        return await self.repo.create(
            email=email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_active=data.is_active,
            is_superuser=data.is_superuser,
            roles=roles,
        )

    async def update(self, user_id: uuid.UUID, data: UserUpdate | UserUpdateSelf) -> User:
        user = await self.get(user_id)
        values = data.model_dump(exclude_unset=True)
        if password := values.pop("password", None):
            values["hashed_password"] = hash_password(password)
        if email := values.get("email"):
            values["email"] = email.lower()
            if email.lower() != user.email and await self.repo.exists(email=email.lower()):
                raise ConflictError("Email already registered")
        return await self.repo.update(user, **values)

    async def delete(self, user_id: uuid.UUID) -> None:
        await self.repo.delete(await self.get(user_id))

    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        user, role = await self.get(user_id), await self.roles.get(role_id)
        if role not in user.roles:
            user.roles.append(role)
            await self.session.flush()
            await self.session.refresh(user)
        return user

    async def revoke_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        user, role = await self.get(user_id), await self.roles.get(role_id)
        if role in user.roles:
            user.roles.remove(role)
            await self.session.flush()
            await self.session.refresh(user)
        return user
