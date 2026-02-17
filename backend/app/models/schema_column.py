"""Schema column metadata — normalized."""

import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, BigInteger, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SchemaColumn(BaseModel):
    __tablename__ = "schema_columns"
    __table_args__ = (
        {"info": {"unique_together": ("schema_table_id", "column_name")}},
    )

    schema_table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schema_tables.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, default=False)
    fk_references: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ordinal_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_business_term: Mapped[str | None] = mapped_column(String(255), nullable=True)
    distinct_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    null_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    schema_table = relationship("SchemaTable", back_populates="columns")
