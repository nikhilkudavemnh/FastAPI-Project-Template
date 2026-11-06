import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_token, decode_token, verify_password
from app.modules.auth.schemas import RegisterRequest, TokenPair
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.settings = settings
        self.users = UserService(session)

    def issue_tokens(self, user: User) -> TokenPair:
        sub = str(user.id)
        return TokenPair(
            access_token=create_token(
                self.settings,
                subject=sub,
                token_type="access",
                extra={"roles": sorted(user.role_names)},
            ),
            refresh_token=create_token(self.settings, subject=sub, token_type="refresh"),
        )

    async def register(self, data: RegisterRequest) -> User:
        default_role = await self.users.roles.get_by_name("user")
        return await self.users.create(
            UserCreate(
                email=data.email,
                password=data.password,
                full_name=data.full_name,
                role_names=[default_role.name] if default_role else [],
            )
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedError("Inactive user")
        return user

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(self.settings, refresh_token, expected_type="refresh")
        user = await self.users.repo.get(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User no longer valid")
        return self.issue_tokens(user)
