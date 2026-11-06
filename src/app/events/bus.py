"""Minimal in-process event bus with the same shape you'd give a Redis Streams / Kafka /
NATS adapter. Services publish domain events; other modules (or other services, once a
broker-backed bus is dropped in) subscribe by event name."""

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

type Handler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Event:
    name: str
    payload: dict[str, Any]
    source: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus(Protocol):
    async def publish(self, event: Event) -> None: ...

    def subscribe(self, name: str, handler: Handler) -> None: ...


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, name: str, handler: Handler) -> None:
        self._handlers[name].append(handler)

    async def publish(self, event: Event) -> None:
        handlers = self._handlers.get(event.name, [])
        await asyncio.gather(*(h(event) for h in handlers), return_exceptions=True)


bus: EventBus = InMemoryEventBus()
