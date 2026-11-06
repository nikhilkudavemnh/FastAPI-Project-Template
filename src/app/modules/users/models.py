from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.roles.models import Role, user_roles


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles, back_populates="users", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    @property
    def role_names(self) -> set[str]:
        return {r.name for r in self.roles}

    @property
    def permissions(self) -> set[str]:
        return {p for r in self.roles for p in r.permissions}

    def has_permission(self, permission: str) -> bool:
        return self.is_superuser or "*" in self.permissions or permission in self.permissions

    def has_role(self, role: str) -> bool:
        return self.is_superuser or role in self.role_names
