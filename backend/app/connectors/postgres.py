"""PostgreSQL connector using asyncpg."""

import time
import asyncpg
from app.connectors.base import BaseConnector, TableInfo, ColumnInfo, QueryResult
from loguru import logger


class PostgreSQLConnector(BaseConnector):
    def __init__(self, host: str, port: int, database: str, username: str, password: str, ssl_mode: str = "prefer"):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl_mode = ssl_mode
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=1,
                max_size=5,
                command_timeout=30,
            )
        return self._pool

    async def test_connection(self) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False

    async def get_tables(self) -> list[TableInfo]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT t.table_name, t.table_type,
                       (SELECT reltuples::bigint FROM pg_class WHERE relname = t.table_name) as row_count
                FROM information_schema.tables t
                WHERE t.table_schema = 'public'
                  AND t.table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY t.table_name
            """)
            return [
                TableInfo(
                    name=row["table_name"],
                    table_type="view" if row["table_type"] == "VIEW" else "table",
                    row_count=row["row_count"],
                )
                for row in rows
            ]

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable = 'YES' as is_nullable,
                    c.ordinal_position,
                    EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                          AND tc.table_name = c.table_name
                          AND ccu.column_name = c.column_name
                    ) as is_primary_key,
                    EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                          AND tc.table_name = c.table_name
                          AND kcu.column_name = c.column_name
                    ) as is_foreign_key,
                    (
                        SELECT ccu2.table_name || '.' || ccu2.column_name
                        FROM information_schema.referential_constraints rc
                        JOIN information_schema.key_column_usage kcu ON rc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage ccu2 ON rc.unique_constraint_name = ccu2.constraint_name
                        WHERE kcu.table_name = c.table_name AND kcu.column_name = c.column_name
                        LIMIT 1
                    ) as fk_references
                FROM information_schema.columns c
                WHERE c.table_name = $1 AND c.table_schema = 'public'
                ORDER BY c.ordinal_position
            """, table_name)
            return [
                ColumnInfo(
                    name=row["column_name"],
                    data_type=row["data_type"],
                    is_nullable=row["is_nullable"],
                    is_primary_key=row["is_primary_key"],
                    is_foreign_key=row["is_foreign_key"],
                    fk_references=row["fk_references"],
                    ordinal_position=row["ordinal_position"],
                )
                for row in rows
            ]

    async def execute_query(self, sql: str, timeout: int = 30, max_rows: int = 10000) -> QueryResult:
        start = time.perf_counter()
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(f"SET statement_timeout = '{timeout * 1000}'")
                rows = await conn.fetch(sql)
                elapsed = int((time.perf_counter() - start) * 1000)

                if not rows:
                    return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed)

                columns = list(rows[0].keys())
                data = [list(row.values()) for row in rows[:max_rows]]
                return QueryResult(
                    columns=columns,
                    rows=data,
                    row_count=len(data),
                    execution_time_ms=elapsed,
                )
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed, error=str(e))

    async def get_sample_values(self, table: str, column: str, limit: int = 10) -> list:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL LIMIT $1',
                limit,
            )
            return [row[column] for row in rows]

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
