"""Export request schemas."""

import uuid
from typing import Optional
from pydantic import BaseModel


class ExportRequest(BaseModel):
    query_sql: str
    connection_id: uuid.UUID
    title: Optional[str] = "DataMind Export"
    include_chart: bool = True
