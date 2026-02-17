"""SQLite connector using aiosqlite."""

import time
import aiosqlite
from app.connectors.base import BaseConnector, TableInfo, ColumnInfo, QueryResult
from loguru import logger


class SQLiteConnector(BaseConnector):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._conn = None

    async def _get_conn(self):
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.file_path)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def test_connection(self) -> bool:
        try:
            conn = await self._get_conn()
            await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite connection test failed: {e}")
            return False

    async def get_tables(self) -> list[TableInfo]:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'"
        )
        rows = await cursor.fetchall()
        tables = []
        for row in rows:
            count_cursor = await conn.execute(f'SELECT COUNT(*) FROM "{row[0]}"')
            count = await count_cursor.fetchone()
            tables.append(TableInfo(name=row[0], table_type=row[1], row_count=count[0] if count else 0))
        return tables

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        conn = await self._get_conn()
        cursor = await conn.execute(f'PRAGMA table_info("{table_name}")')
        rows = await cursor.fetchall()
        return [
            ColumnInfo(
                name=row[1],
                data_type=row[2] or "TEXT",
                is_nullable=not row[3],
                is_primary_key=bool(row[5]),
                is_foreign_key=False,
                fk_references=None,
                ordinal_position=row[0],
            )
            for row in rows
        ]

    async def execute_query(self, sql: str, timeout: int = 30, max_rows: int = 10000) -> QueryResult:
        start = time.perf_counter()
        conn = await self._get_conn()
        try:
            cursor = await conn.execute(sql)
            rows = await cursor.fetchmany(max_rows)
            elapsed = int((time.perf_counter() - start) * 1000)

            if not rows or cursor.description is None:
                return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed)

            columns = [desc[0] for desc in cursor.description]
            data = [list(row) for row in rows]
            return QueryResult(columns=columns, rows=data, row_count=len(data), execution_time_ms=elapsed)
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed, error=str(e))

    async def get_sample_values(self, table: str, column: str, limit: int = 10) -> list:
        conn = await self._get_conn()
        cursor = await conn.execute(
            f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL LIMIT ?',
            (limit,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
