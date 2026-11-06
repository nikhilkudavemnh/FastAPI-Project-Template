from app.modules.auth.router import router
from app.modules.registry import Module

module = Module(name="auth", router=router)
