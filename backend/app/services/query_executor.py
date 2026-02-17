"""Safe SQL execution: sqlglot parse → read-only user → timeout."""

import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.sql_validator import SQLSafetyValidator
from app.core.constants import MAX_QUERY_ROWS, QUERY_TIMEOUT_SECONDS
from loguru import logger


class QueryExecutor:
    """Executes validated SQL against user databases with safety controls."""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.validator = SQLSafetyValidator()

    async def execute(
        self,
        connection_id: str,
        sql: str,
        db: AsyncSession,
        timeout_seconds: int = QUERY_TIMEOUT_SECONDS,
        max_rows: int = MAX_QUERY_ROWS,
    ) -> dict:
        """Execute SQL with safety validation and resource limits."""
        # Validate SQL
        validation = self.validator.validate(sql)
        if not validation["is_safe"]:
            return {
                "data": {"columns": [], "rows": [], "row_count": 0},
                "error": f"SQL validation failed: {validation['reason']}",
                "execution_time_ms": 0,
            }

        try:
            connector = await self.connection_manager.get_connector(connection_id, db)

            start = time.perf_counter()
            result = await connector.execute_query(
                sql=validation.get("parsed_sql", sql),
                timeout=timeout_seconds,
                max_rows=max_rows,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            if result.error:
                return {
                    "data": {"columns": [], "rows": [], "row_count": 0},
                    "error": result.error,
                    "execution_time_ms": elapsed_ms,
                }

            return {
                "data": {
                    "columns": result.columns,
                    "rows": result.rows,
                    "row_count": result.row_count,
                },
                "error": None,
                "execution_time_ms": elapsed_ms,
            }

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {
                "data": {"columns": [], "rows": [], "row_count": 0},
                "error": str(e),
                "execution_time_ms": 0,
            }
