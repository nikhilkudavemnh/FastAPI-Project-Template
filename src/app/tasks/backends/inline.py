"""Runs tasks in the current process on the event loop. Good for dev, tests, and services
that only need fire-and-forget work without extra infrastructure."""

import asyncio
import uuid
from typing import Any

from app.core.logging import get_logger
from app.tasks.base import TaskBackend, TaskHandle, registry

log = get_logger(__name__)


class InlineBackend(TaskBackend):
    name = "inline"

    def __init__(self) -> None:
        self._pending: set[asyncio.Task[Any]] = set()

    async def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> TaskHandle:
        registry.get(task_name)  # fail fast on unknown task
        handle = TaskHandle(id=uuid.uuid4().hex, name=task_name, backend=self.name)
        t = asyncio.create_task(self._run(handle, *args, **kwargs))
        self._pending.add(t)
        t.add_done_callback(self._pending.discard)
        return handle

    async def _run(self, handle: TaskHandle, *args: Any, **kwargs: Any) -> None:
        try:
            await registry.run(handle.name, *args, **kwargs)
            log.info("task_done", task=handle.name, task_id=handle.id)
        except Exception:
            log.exception("task_failed", task=handle.name, task_id=handle.id)

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)

    async def drain(self) -> None:
        """Test helper: wait for everything enqueued so far."""
        await self.shutdown()
