"""Dashboard and Widget request/response schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Dashboard Schemas ────────────────────────────────────────────────────────

class DashboardCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class DashboardUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_shared: Optional[bool] = None
    layout_config: Optional[dict] = None


class DashboardResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    is_shared: bool
    layout_config: dict
    created_at: datetime
    updated_at: Optional[datetime] = None
    widget_count: int = 0

    model_config = {"from_attributes": True}


# ── Widget Schemas ───────────────────────────────────────────────────────────

class WidgetCreate(BaseModel):
    title: str = Field(..., max_length=255)
    widget_type: str
    query_sql: str
    connection_id: uuid.UUID
    chart_config: dict = {}
    refresh_interval_seconds: int = 300


class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    widget_type: Optional[str] = None
    chart_config: Optional[dict] = None
    position: Optional[dict] = None
    refresh_interval_seconds: Optional[int] = None
    query_sql: Optional[str] = None


class WidgetResponse(BaseModel):
    id: uuid.UUID
    title: str
    widget_type: str
    query_sql: Optional[str] = None
    connection_id: Optional[uuid.UUID] = None
    chart_config: dict
    position: dict
    refresh_interval_seconds: int = 300
    last_refreshed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Compound Schemas ─────────────────────────────────────────────────────────

class DashboardWithWidgets(DashboardResponse):
    widgets: list[WidgetResponse] = []

    model_config = {"from_attributes": True}


class WidgetRefreshResponse(BaseModel):
    widget_id: uuid.UUID
    query_result_preview: Optional[dict] = None
    last_refreshed_at: Optional[datetime] = None
    error: Optional[str] = None


# ── Pin-from-Chat Schemas ────────────────────────────────────────────────────

class PinFromChatRequest(BaseModel):
    message_id: uuid.UUID
    dashboard_id: uuid.UUID
    title: Optional[str] = None
