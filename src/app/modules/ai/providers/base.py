"""Provider-agnostic AI interface. Implement `AIProvider` for any vendor/model, register it,
and every AI use case (chat, RAG, extraction, classification...) composes on top of it."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


@runtime_checkable
class AIProvider(Protocol):
    name: str

    async def complete(self, messages: list[Message], **options: Any) -> Completion: ...

    def stream(self, messages: list[Message], **options: Any) -> AsyncIterator[str]: ...

    async def embed(self, texts: list[str], **options: Any) -> list[list[float]]: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._default: str | None = None

    def register(self, provider: AIProvider, *, default: bool = False) -> None:
        self._providers[provider.name] = provider
        if default or self._default is None:
            self._default = provider.name

    def get(self, name: str | None = None) -> AIProvider:
        key = name or self._default
        if key is None or key not in self._providers:
            raise LookupError(f"AI provider '{key}' is not registered")
        return self._providers[key]

    def names(self) -> list[str]:
        return list(self._providers)


providers = ProviderRegistry()
