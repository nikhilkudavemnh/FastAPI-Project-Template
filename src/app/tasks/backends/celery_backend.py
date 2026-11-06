"""Celery slot. NOT implemented on purpose; wire it when you need a real worker fleet.

Steps to enable:
  1. uv add "celery[redis]"           (or uncomment it in the `workers` group)
  2. Create the Celery app:
         celery_app = Celery(settings.service_name, broker=settings.redis_url, backend=...)
  3. Expose one generic Celery task that dispatches into our registry:
         @celery_app.task(name="app.dispatch")
         def dispatch(task_name, args, kwargs):
             asyncio.run(registry.run(task_name, *args, **kwargs))
  4. Implement `enqueue` as `celery_app.send_task("app.dispatch", args=[task_name, args, kwargs])`
  5. Point `python -m app.worker` at `celery_app.worker_main([...])` and set TASK_BACKEND=celery.

Because tasks are registered by *name* in `app.tasks.registry`, no task code changes.
"""

from typing import Any

from app.tasks.base import TaskBackend, TaskHandle


class CeleryBackend(TaskBackend):
    name = "celery"

    def __init__(self, broker_url: str | None) -> None:
        self.broker_url = broker_url

    async def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> TaskHandle:
        raise NotImplementedError(
            "Celery backend is a stub. See app/tasks/backends/celery_backend.py to enable it."
        )

    async def startup(self) -> None:
        raise NotImplementedError("Celery backend not wired yet (see module docstring).")

    async def shutdown(self) -> None:
        pass
