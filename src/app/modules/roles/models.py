import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.modules.users.models import User

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    # Flat permission strings, e.g. "users:read", "ai:invoke". "*" grants everything.
    permissions: Mapped[list[str]] = mapped_column(default=list)

    # write_only: never implicitly loaded (async-safe); query via role.users.select()
    users: WriteOnlyMapped[User] = relationship(secondary=user_roles, back_populates="roles")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"

    def has_permission(self, permission: str) -> bool:
        return "*" in self.permissions or permission in self.permissions


__all__ = ["Role", "user_roles", "uuid"]
