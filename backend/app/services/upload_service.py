"""CSV/Excel upload → SQLite ingestion pipeline."""

import os
import uuid
import aiosqlite
import pandas as pd
from loguru import logger


class UploadService:
    """Handles CSV/Excel file uploads by converting to SQLite databases."""

    UPLOAD_DIR = "uploads"

    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    async def ingest_csv(self, file_content: bytes, filename: str) -> dict:
        """Convert CSV to SQLite database."""
        return await self._ingest_file(file_content, filename, "csv")

    async def ingest_excel(self, file_content: bytes, filename: str) -> dict:
        """Convert Excel to SQLite database."""
        return await self._ingest_file(file_content, filename, "excel")

    async def _ingest_file(self, file_content: bytes, filename: str, file_type: str) -> dict:
        """Ingest file into a SQLite database."""
        import io

        file_id = str(uuid.uuid4())
        db_path = os.path.join(self.UPLOAD_DIR, f"{file_id}.db")
        table_name = os.path.splitext(filename)[0].replace(" ", "_").replace("-", "_").lower()

        try:
            if file_type == "csv":
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))

            # Write to SQLite
            import sqlite3
            conn = sqlite3.connect(db_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            conn.close()

            return {
                "file_id": file_id,
                "db_path": db_path,
                "table_name": table_name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
            }
        except Exception as e:
            logger.error(f"File ingestion error: {e}")
            raise
