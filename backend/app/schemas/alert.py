"""Alert request/response schemas."""

import uuid
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    connection_id: uuid.UUID
    query_sql: str
    condition_type: str = Field(..., pattern=r"^(above|below|change_pct|anomaly)$")
    threshold_value: Optional[Decimal] = None
    check_interval_minutes: int = 60


class AlertResponse(BaseModel):
    id: uuid.UUID
    name: str
    condition_type: str
    is_active: bool
    last_checked_at: Optional[str]
    last_value: Optional[Decimal]
    consecutive_failures: int

    model_config = {"from_attributes": True}
