"""Celery task: periodic schema refresh."""

from app.tasks.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.tasks.schema_refresh.refresh_all_schemas")
def refresh_all_schemas():
    """Refresh schema metadata for all active connections."""
    logger.info("Running schema refresh cycle...")
    # TODO: Implement schema refresh
    # 1. Query all active connections
    # 2. Introspect each database
    # 3. Update schema_tables and schema_columns
    # 4. Diff detection for changes
    logger.info("Schema refresh cycle complete")
