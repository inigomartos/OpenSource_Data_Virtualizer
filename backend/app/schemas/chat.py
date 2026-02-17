"""Chat request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    connection_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    is_pinned: Optional[bool] = None


# ── Response Schemas ─────────────────────────────────────────────────────────

class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    generated_sql: Optional[str] = None
    chart_config: Optional[dict] = None
    query_result_preview: Optional[dict] = None
    full_result_row_count: Optional[int] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """REST fallback response for /message endpoint."""
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
    title: Optional[str] = None
    connection_id: Optional[uuid.UUID] = None
    is_pinned: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
