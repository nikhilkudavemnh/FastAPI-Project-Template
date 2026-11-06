from app.modules.registry import Module
from app.modules.users.router import router

module = Module(name="users", router=router)
