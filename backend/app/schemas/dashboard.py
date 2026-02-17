"""Dashboard request/response schemas."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field


class DashboardCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class DashboardResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    is_shared: bool
    layout_config: dict
    created_at: str

    model_config = {"from_attributes": True}


class WidgetCreate(BaseModel):
    title: str = Field(..., max_length=255)
    widget_type: str
    query_sql: str
    connection_id: uuid.UUID
    chart_config: dict = {}
    refresh_interval_seconds: int = 300


class WidgetResponse(BaseModel):
    id: uuid.UUID
    title: str
    widget_type: str
    chart_config: dict
    position: dict
    last_error: Optional[str]

    model_config = {"from_attributes": True}
