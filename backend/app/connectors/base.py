"""Abstract connector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TableInfo:
    name: str
    table_type: str  # 'table' | 'view'
    row_count: int | None


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    fk_references: str | None
    ordinal_position: int


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list]
    row_count: int
    execution_time_ms: int
    error: str | None = None


class BaseConnector(ABC):
    """Every data connector must implement these methods."""

    @abstractmethod
    async def test_connection(self) -> bool: ...

    @abstractmethod
    async def get_tables(self) -> list[TableInfo]: ...

    @abstractmethod
    async def get_columns(self, table_name: str) -> list[ColumnInfo]: ...

    @abstractmethod
    async def execute_query(self, sql: str, timeout: int = 30, max_rows: int = 10000) -> QueryResult: ...

    @abstractmethod
    async def get_sample_values(self, table: str, column: str, limit: int = 10) -> list: ...

    @abstractmethod
    async def close(self) -> None: ...
