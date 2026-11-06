from app.modules.ai.providers.base import providers
from app.modules.ai.providers.echo import EchoProvider
from app.modules.ai.router import router
from app.modules.registry import Module


def _setup() -> None:
    # Register real providers here, e.g. based on settings / env keys.
    providers.register(EchoProvider(), default=True)


module = Module(name="ai", router=router, on_startup=_setup)
