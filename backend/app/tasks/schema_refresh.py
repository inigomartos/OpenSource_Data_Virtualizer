"""Celery task: periodic schema refresh for all active connections."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app
from app.core.database import async_session_factory
from app.models.connection import Connection
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.services.connection_manager import ConnectionManager
from app.services.schema_discoverer import SchemaDiscoverer
from loguru import logger

connection_manager = ConnectionManager()
schema_discoverer = SchemaDiscoverer()


async def _refresh_single_connection(connection: Connection, db: AsyncSession) -> dict:
    """Refresh schema for a single connection. Returns a summary dict."""
    conn_id = str(connection.id)
    summary = {
        "connection_id": conn_id,
        "connection_name": connection.name,
        "tables_before": 0,
        "tables_after": 0,
        "new_tables": [],
        "removed_tables": [],
        "error": None,
    }

    try:
        # Count existing tables before refresh
        existing_result = await db.execute(
            select(SchemaTable).where(SchemaTable.connection_id == connection.id)
        )
        existing_tables = existing_result.scalars().all()
        existing_table_names = {t.table_name for t in existing_tables}
        summary["tables_before"] = len(existing_table_names)

        # Get connector
        connector = await connection_manager.get_connector(conn_id, db)

        try:
            # Introspect current schema from the live database
            live_tables = await connector.get_tables()
            live_table_names = {t.name for t in live_tables}

            # Detect new tables
            new_table_names = live_table_names - existing_table_names
            summary["new_tables"] = list(new_table_names)

            # Detect removed tables
            removed_table_names = existing_table_names - live_table_names
            summary["removed_tables"] = list(removed_table_names)

            # Remove tables that no longer exist in the live database
            for table in existing_tables:
                if table.table_name in removed_table_names:
                    await db.delete(table)

            # Use the schema discoverer to upsert tables and columns
            await schema_discoverer.discover_schema(conn_id, connector, db)

            # Update connection's last_synced_at
            connection.last_synced_at = datetime.now(timezone.utc)

            # Count tables after refresh
            after_result = await db.execute(
                select(SchemaTable).where(SchemaTable.connection_id == connection.id)
            )
            after_tables = after_result.scalars().all()
            summary["tables_after"] = len(after_tables)

        finally:
            await connector.close()

    except Exception as e:
        logger.error(f"Schema refresh failed for connection {conn_id} ({connection.name}): {e}")
        summary["error"] = str(e)

    return summary


async def _run_schema_refresh_cycle() -> None:
    """Main async logic: query all active connections and refresh schemas."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Connection).where(Connection.is_active == True)
            )
            connections = result.scalars().all()

            if not connections:
                logger.debug("No active connections to refresh")
                return

            logger.info(f"Refreshing schemas for {len(connections)} active connections")

            summaries = []
            for connection in connections:
                summary = await _refresh_single_connection(connection, db)
                summaries.append(summary)

                if summary["new_tables"]:
                    logger.info(
                        f"Connection '{connection.name}': {len(summary['new_tables'])} new tables: "
                        f"{', '.join(summary['new_tables'])}"
                    )
                if summary["removed_tables"]:
                    logger.info(
                        f"Connection '{connection.name}': {len(summary['removed_tables'])} removed tables: "
                        f"{', '.join(summary['removed_tables'])}"
                    )
                if summary["error"]:
                    logger.warning(
                        f"Connection '{connection.name}': refresh failed: {summary['error']}"
                    )

            await db.commit()

            # Log overall summary
            total_ok = sum(1 for s in summaries if s["error"] is None)
            total_err = sum(1 for s in summaries if s["error"] is not None)
            total_new = sum(len(s["new_tables"]) for s in summaries)
            total_removed = sum(len(s["removed_tables"]) for s in summaries)

            logger.info(
                f"Schema refresh cycle complete: {total_ok} succeeded, {total_err} failed, "
                f"{total_new} new tables, {total_removed} removed tables"
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Schema refresh cycle failed: {e}")
            raise


@celery_app.task(name="app.tasks.schema_refresh.refresh_all_schemas")
def refresh_all_schemas():
    """Refresh schema metadata for all active connections."""
    logger.info("Running schema refresh cycle...")
    asyncio.run(_run_schema_refresh_cycle())
    logger.info("Schema refresh cycle complete")
