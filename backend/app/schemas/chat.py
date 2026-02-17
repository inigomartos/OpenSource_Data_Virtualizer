"""Chat request/response schemas."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    connection_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class ChatResponse(BaseModel):
    content: str
    context_summary: Optional[str] = None
    generated_sql: Optional[str] = None
    query_result_preview: Optional[dict] = None
    full_result_row_count: Optional[int] = None
    chart_config: Optional[dict] = None
    execution_time_ms: Optional[int] = None
    token_usage: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    connection_id: Optional[uuid.UUID]
    is_pinned: bool
    created_at: str

    model_config = {"from_attributes": True}
