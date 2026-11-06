"""Zero-dependency provider used for tests and local dev. Replace/add real providers in
this package (e.g. anthropic.py, openai.py, ollama.py) and register them in module.py."""

from collections.abc import AsyncIterator
from typing import Any

from app.modules.ai.providers.base import AIProvider, Completion, Message


class EchoProvider(AIProvider):
    name = "echo"

    async def complete(self, messages: list[Message], **options: Any) -> Completion:
        last = messages[-1].content if messages else ""
        return Completion(text=f"echo: {last}", model="echo-1", usage={"input": len(last)})

    async def stream(self, messages: list[Message], **options: Any) -> AsyncIterator[str]:
        for word in (await self.complete(messages)).text.split(" "):
            yield word + " "

    async def embed(self, texts: list[str], **options: Any) -> list[list[float]]:
        return [[float(len(t))] for t in texts]
