from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern=r"^(system|user|assistant|tool)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    provider: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    text: str
    model: str
    provider: str
    usage: dict[str, int]


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=256)
    provider: str | None = None


class EmbedResponse(BaseModel):
    vectors: list[list[float]]
    provider: str
