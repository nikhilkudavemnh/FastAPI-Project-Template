"""Import every module's models so Base.metadata is complete for Alembic and tests.
Add a line here when you add a module with tables."""

from app.db.base import Base
from app.modules.roles.models import Role, user_roles
from app.modules.users.models import User

__all__ = ["Base", "Role", "User", "user_roles"]
