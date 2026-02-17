"""Dashboard widget model."""

import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Widget(BaseModel):
    __tablename__ = "widgets"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_sql: Mapped[str] = mapped_column(Text, nullable=False)
    chart_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    refresh_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    position: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")
    connection = relationship("Connection", back_populates="widgets")
