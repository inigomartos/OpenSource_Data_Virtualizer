"""Connection request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(..., pattern=r"^(postgresql|mysql|sqlite|csv|excel)$")
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: str = "prefer"
    file_path: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    tables_found: Optional[int] = None
