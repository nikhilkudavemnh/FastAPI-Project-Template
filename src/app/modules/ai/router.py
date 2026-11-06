from fastapi import APIRouter

from app.api.deps import require_permissions
from app.modules.ai.providers.base import providers
from app.modules.ai.schemas import ChatRequest, ChatResponse, EmbedRequest, EmbedResponse
from app.modules.ai.service import AIService

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[require_permissions("ai:invoke")])


@router.get("/providers", response_model=list[str])
async def list_providers() -> list[str]:
    return providers.names()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    return await AIService(providers).chat(req)


@router.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    return await AIService(providers).embed(req)
