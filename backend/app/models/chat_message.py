"""Chat message model with result preview and context summary."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ChatMessage(Base):
    """Chat message — no updated_at needed (messages are immutable)."""
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI metadata
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    sql_was_executed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Result preview (max 100 rows)
    query_result_preview: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    full_result_row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Visualization
    chart_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Performance
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Errors
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cost tracking
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Condensed summary for conversation context
    context_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
