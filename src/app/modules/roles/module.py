from app.modules.registry import Module
from app.modules.roles.router import router

module = Module(name="roles", router=router)
