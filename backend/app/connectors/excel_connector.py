"""Excel connector: loads Excel → temp SQLite and wraps SQLiteConnector."""

import os
import pandas as pd
from app.connectors.sqlite import SQLiteConnector
from app.connectors.base import BaseConnector, TableInfo, ColumnInfo, QueryResult


class ExcelConnector(BaseConnector):
    """Loads an Excel file into a temporary SQLite database for querying."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        db_path = file_path.rsplit(".", 1)[0] + ".db"

        # Load all sheets into SQLite
        import sqlite3
        conn = sqlite3.connect(db_path)
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            table_name = sheet_name.replace(" ", "_").lower()
            df.to_sql(table_name, conn, if_exists="replace", index=False)
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
