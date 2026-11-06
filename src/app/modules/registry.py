"""Module registry. A Module is a bounded context: router + optional startup hook.
`ENABLED_MODULES` chooses which ones a process mounts, so the same codebase/image runs as a
monolith (all modules) or as N microservices (one or a few modules each)."""

import importlib
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    router: APIRouter
    on_startup: Callable[[], None] | None = None


def load_modules(names: list[str]) -> list[Module]:
    modules: list[Module] = []
    for name in names:
        mod = importlib.import_module(f"app.modules.{name}.module")
        module: Module = mod.module
        modules.append(module)
        log.debug("module_loaded", module=module.name)
    return modules
