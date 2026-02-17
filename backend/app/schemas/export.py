"""Export request schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    title: str = Field(default="DataMind Export", max_length=255)
    data: dict  # Expected shape: {"columns": list[str], "rows": list[list]}
    insight: Optional[str] = None
    chart_config: Optional[dict] = None
