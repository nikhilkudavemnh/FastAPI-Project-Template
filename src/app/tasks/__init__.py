from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings
from app.tasks.base import TaskBackend, TaskHandle, registry, task


def build_backend(settings: Settings) -> TaskBackend:
    match settings.task_backend:
        case "inline":
            from app.tasks.backends.inline import InlineBackend

            return InlineBackend()
        case "celery":
            from app.tasks.backends.celery_backend import CeleryBackend

            return CeleryBackend(settings.redis_url)
    raise ValueError(f"Unknown TASK_BACKEND={settings.task_backend!r}")


@lru_cache
def get_backend() -> TaskBackend:
    return build_backend(get_settings())


async def enqueue(task_name: str, *args: Any, **kwargs: Any) -> TaskHandle:
    return await get_backend().enqueue(task_name, *args, **kwargs)


__all__ = [
    "TaskBackend",
    "TaskHandle",
    "build_backend",
    "enqueue",
    "get_backend",
    "registry",
    "task",
]
