"""Backend-agnostic task queue.

Usage:
    from app.tasks import task, enqueue

    @task("emails.send_welcome")
    async def send_welcome(user_id: str) -> None: ...

    await enqueue("emails.send_welcome", user_id=str(user.id))

The backend is selected by TASK_BACKEND. `inline` runs the coroutine in-process (dev/test).
To add Celery/arq/etc: implement `TaskBackend` in tasks/backends/, map it in `get_backend`.
"""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

type TaskFn = Callable[..., Awaitable[Any] | Any]


@dataclass(frozen=True, slots=True)
class TaskHandle:
    id: str
    name: str
    backend: str


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskFn] = {}

    def register(self, name: str, fn: TaskFn) -> None:
        if name in self._tasks:
            raise ValueError(f"Task '{name}' already registered")
        self._tasks[name] = fn

    def get(self, name: str) -> TaskFn:
        try:
            return self._tasks[name]
        except KeyError as e:
            raise LookupError(f"Unknown task '{name}'") from e

    def names(self) -> list[str]:
        return list(self._tasks)

    async def run(self, name: str, *args: Any, **kwargs: Any) -> Any:
        fn = self.get(name)
        result = fn(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return await asyncio.to_thread(lambda: result)


registry = TaskRegistry()


def task(name: str) -> Callable[[TaskFn], TaskFn]:
    def deco(fn: TaskFn) -> TaskFn:
        registry.register(name, fn)
        return fn

    return deco


class TaskBackend(Protocol):
    name: str

    async def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> TaskHandle: ...

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...
