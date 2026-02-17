"""MySQL connector using aiomysql."""

import time
import aiomysql
from app.connectors.base import BaseConnector, TableInfo, ColumnInfo, QueryResult
from loguru import logger


class MySQLConnector(BaseConnector):
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                db=self.database,
                user=self.username,
                password=self.password,
                minsize=1,
                maxsize=5,
            )
        return self._pool

    async def test_connection(self) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            return False

    async def get_tables(self) -> list[TableInfo]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT TABLE_NAME as table_name, TABLE_TYPE as table_type, TABLE_ROWS as row_count
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME
                """, (self.database,))
                rows = await cur.fetchall()
                return [
                    TableInfo(
                        name=row["table_name"],
                        table_type="view" if "VIEW" in row["table_type"] else "table",
                        row_count=row["row_count"],
                    )
                    for row in rows
                ]

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION, COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (self.database, table_name))
                rows = await cur.fetchall()
                return [
                    ColumnInfo(
                        name=row["COLUMN_NAME"],
                        data_type=row["DATA_TYPE"],
                        is_nullable=row["IS_NULLABLE"] == "YES",
                        is_primary_key=row["COLUMN_KEY"] == "PRI",
                        is_foreign_key=row["COLUMN_KEY"] == "MUL",
                        fk_references=None,
                        ordinal_position=row["ORDINAL_POSITION"],
                    )
                    for row in rows
                ]

    async def execute_query(self, sql: str, timeout: int = 30, max_rows: int = 10000) -> QueryResult:
        start = time.perf_counter()
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(f"SET SESSION MAX_EXECUTION_TIME = {timeout * 1000}")
                    await cur.execute(sql)
                    rows = await cur.fetchmany(max_rows)
                    elapsed = int((time.perf_counter() - start) * 1000)

                    if not rows:
                        return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed)

                    columns = list(rows[0].keys())
                    data = [list(row.values()) for row in rows]
                    return QueryResult(columns=columns, rows=data, row_count=len(data), execution_time_ms=elapsed)
        except Exception as e:
            elapsed = int((time.perf_counter() - start) * 1000)
            return QueryResult(columns=[], rows=[], row_count=0, execution_time_ms=elapsed, error=str(e))

    async def get_sample_values(self, table: str, column: str, limit: int = 10) -> list:
        escaped_column = column.replace('`', '``')
        escaped_table = table.replace('`', '``')
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT DISTINCT `{escaped_column}` FROM `{escaped_table}` WHERE `{escaped_column}` IS NOT NULL LIMIT %s",
                    (limit,),
                )
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    async def close(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
