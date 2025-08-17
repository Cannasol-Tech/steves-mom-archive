from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1)
    model: Optional[str] = None  # e.g. 'grok-3-mini'
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 512
    stream_reasoning: bool = False


class ChatResponse(BaseModel):
    message: ChatMessage
    provider: str
    model: str
    response_time_ms: Optional[int] = None
    reasoning_content: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
