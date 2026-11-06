"""Use-case layer. Add one method (or one class) per AI use case: summarize, extract,
classify, RAG query... They all depend on `AIProvider`, never on a vendor SDK."""

from app.modules.ai.providers.base import Message, ProviderRegistry
from app.modules.ai.schemas import ChatRequest, ChatResponse, EmbedRequest, EmbedResponse


class AIService:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def chat(self, req: ChatRequest) -> ChatResponse:
        provider = self.registry.get(req.provider)
        result = await provider.complete(
            [Message(role=m.role, content=m.content) for m in req.messages], **req.options
        )
        return ChatResponse(
            text=result.text, model=result.model, provider=provider.name, usage=result.usage
        )

    async def embed(self, req: EmbedRequest) -> EmbedResponse:
        provider = self.registry.get(req.provider)
        return EmbedResponse(vectors=await provider.embed(req.texts), provider=provider.name)
