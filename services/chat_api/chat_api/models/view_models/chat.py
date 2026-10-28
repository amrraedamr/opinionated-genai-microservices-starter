from typing import Any

from pydantic import Field

from base.models.view_models import BaseModel


class SendChatRequest(BaseModel):
    content: str


class SendChatResponse(BaseModel):
    content: str


class ChatMessageView(BaseModel):
    role: str
    content: str | None = None
    sequence: int
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ListChatResponse(BaseModel):
    messages: list[ChatMessageView]
