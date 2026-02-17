"""Schema table metadata — normalized from old schema_cache."""

import uuid
from sqlalchemy import String, BigInteger, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SchemaTable(BaseModel):
    __tablename__ = "schema_tables"
    __table_args__ = (
        UniqueConstraint("connection_id", "table_name", name="uq_schema_table_conn_name"),
    )

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_type: Mapped[str] = mapped_column(String(50), default="table")
    row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    connection = relationship("Connection", back_populates="schema_tables")
    columns = relationship("SchemaColumn", back_populates="schema_table", cascade="all, delete-orphan")
