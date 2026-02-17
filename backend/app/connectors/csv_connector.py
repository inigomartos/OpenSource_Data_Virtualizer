"""CSV connector: loads CSV → temp SQLite and wraps SQLiteConnector."""

import os
import uuid
import pandas as pd
from app.connectors.sqlite import SQLiteConnector
from app.connectors.base import BaseConnector, TableInfo, ColumnInfo, QueryResult


class CSVConnector(BaseConnector):
    """Loads a CSV file into a temporary SQLite database for querying."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        db_path = file_path.rsplit(".", 1)[0] + ".db"
        self.table_name = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_").lower()

        # Load CSV into SQLite
        import sqlite3
        df = pd.read_csv(file_path)
        conn = sqlite3.connect(db_path)
        df.to_sql(self.table_name, conn, if_exists="replace", index=False)
        conn.close()

        self._sqlite = SQLiteConnector(db_path)

    async def test_connection(self) -> bool:
        return await self._sqlite.test_connection()

    async def get_tables(self) -> list[TableInfo]:
        return await self._sqlite.get_tables()

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        return await self._sqlite.get_columns(table_name)

    async def execute_query(self, sql: str, timeout: int = 30, max_rows: int = 10000) -> QueryResult:
        return await self._sqlite.execute_query(sql, timeout, max_rows)

    async def get_sample_values(self, table: str, column: str, limit: int = 10) -> list:
        return await self._sqlite.get_sample_values(table, column, limit)

    async def close(self) -> None:
        await self._sqlite.close()
