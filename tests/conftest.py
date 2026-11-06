"""Test harness: in-memory SQLite, inline task backend, no external services."""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite+aiosqlite://",
        "REDIS_URL": "",
        "JWT_SECRET": "test-secret-must-be-at-least-32-bytes-long!",
        "TASK_BACKEND": "inline",
        "LOG_LEVEL": "WARNING",
        "ENABLED_MODULES": "auth,users,roles,ai",
    }
)

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import get_session
from app.main import create_app
from app.modules.roles.service import RoleService
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService

ADMIN = {"email": "admin@test.io", "password": "adminpass123"}
USER = {"email": "user@test.io", "password": "userpass123"}


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with maker() as s:
        yield s
        await s.rollback()


@pytest.fixture
async def seeded(engine) -> None:
    maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with maker() as s:
        await RoleService(s).ensure_defaults()
        users = UserService(s)
        if await users.get_by_email(ADMIN["email"]) is None:
            await users.create(UserCreate(**ADMIN, is_superuser=True, role_names=["admin"]))
        if await users.get_by_email(USER["email"]) is None:
            await users.create(UserCreate(**USER, role_names=["user"]))
        await s.commit()


@pytest.fixture
async def client(engine, seeded) -> AsyncIterator[AsyncClient]:
    maker = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app = create_app(get_settings())
    app.dependency_overrides[get_session] = _override
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _login(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    r = await client.post(
        "/api/v1/auth/login", data={"username": creds["email"], "password": creds["password"]}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    return await _login(client, ADMIN)


@pytest.fixture
async def user_headers(client: AsyncClient) -> dict[str, str]:
    return await _login(client, USER)
