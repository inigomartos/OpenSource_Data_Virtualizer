"""Alert request/response schemas."""

import uuid
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    connection_id: uuid.UUID
    query_sql: str
    condition_type: str = Field(..., pattern=r"^(above|below|change_pct|anomaly)$")
    threshold_value: Optional[Decimal] = None
    check_interval_minutes: int = Field(default=60, ge=1, le=1440)


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    condition_type: Optional[str] = Field(default=None, pattern=r"^(above|below|change_pct|anomaly)$")
    threshold_value: Optional[Decimal] = None
    check_interval_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    is_active: Optional[bool] = None
    query_sql: Optional[str] = None


class AlertResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    condition_type: str
    threshold_value: Optional[Decimal] = None
    is_active: bool
    last_checked_at: Optional[datetime] = None
    last_value: Optional[Decimal] = None
    consecutive_failures: int
    connection_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertEventResponse(BaseModel):
    id: uuid.UUID
    triggered_value: Decimal
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertWithEvents(AlertResponse):
    events: list[AlertEventResponse] = []

    model_config = {"from_attributes": True}
