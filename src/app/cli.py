"""Operational commands: `python -m app.cli seed`."""

import argparse
import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import get_sessionmaker
from app.modules.roles.service import RoleService
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService

log = get_logger(__name__)


async def seed() -> None:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        await RoleService(session).ensure_defaults()
        users = UserService(session)
        if await users.get_by_email(settings.first_superuser_email) is None:
            await users.create(
                UserCreate(
                    email=settings.first_superuser_email,
                    password=settings.first_superuser_password,
                    full_name="Administrator",
                    is_superuser=True,
                    role_names=["admin"],
                )
            )
            log.info("superuser_created", email=settings.first_superuser_email)
        await session.commit()
    log.info("seed_complete")


def main() -> None:
    configure_logging(get_settings())
    parser = argparse.ArgumentParser(prog="app")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Create default roles and the first superuser")
    args = parser.parse_args()
    if args.command == "seed":
        asyncio.run(seed())


if __name__ == "__main__":
    main()
