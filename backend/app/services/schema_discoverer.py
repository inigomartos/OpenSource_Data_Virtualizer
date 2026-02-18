"""Database schema introspection and AI enrichment."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.models.connection import Connection
from loguru import logger


class SchemaDiscoverer:
    """Introspects connected databases and builds schema context."""

    async def get_schema_context(self, connection_id: str, db: AsyncSession) -> str:
        """Build a text representation of the schema for AI prompts."""
        result = await db.execute(
            select(SchemaTable)
            .where(SchemaTable.connection_id == connection_id)
            .options(selectinload(SchemaTable.columns))
        )
        tables = result.scalars().unique().all()

        if not tables:
            return "No schema metadata available. Please refresh the schema."

        context_parts = []
        for table in tables:
            columns = table.columns

            table_desc = f"### Table: {table.table_name}"
            if table.ai_description:
                table_desc += f"\nDescription: {table.ai_description}"
            if table.row_count:
                table_desc += f"\nRows: ~{table.row_count:,}"

            col_lines = []
            for col in columns:
                line = f"  - {col.column_name} ({col.data_type})"
                if col.is_primary_key:
                    line += " [PK]"
                if col.is_foreign_key and col.fk_references:
                    line += f" [FK → {col.fk_references}]"
                if col.ai_business_term:
                    line += f" — \"{col.ai_business_term}\""
                elif col.ai_description:
                    line += f" — {col.ai_description}"
                if col.sample_values:
                    samples = col.sample_values[:5] if isinstance(col.sample_values, list) else []
                    if samples:
                        line += f" (e.g., {', '.join(str(s) for s in samples)})"
                col_lines.append(line)

            context_parts.append(table_desc + "\n" + "\n".join(col_lines))

        return "\n\n".join(context_parts)

    async def discover_schema(self, connection_id: str, connector, db: AsyncSession) -> None:
        """Introspect a database and store schema metadata."""
        tables = await connector.get_tables()

        for table_info in tables:
            # Upsert table
            result = await db.execute(
                select(SchemaTable).where(
                    SchemaTable.connection_id == connection_id,
                    SchemaTable.table_name == table_info.name,
                )
            )
            schema_table = result.scalar_one_or_none()

            if not schema_table:
                schema_table = SchemaTable(
                    connection_id=connection_id,
                    table_name=table_info.name,
                    table_type=table_info.table_type,
                    row_count=table_info.row_count,
                )
                db.add(schema_table)
                await db.flush()
            else:
                schema_table.row_count = table_info.row_count

            # Get columns
            columns = await connector.get_columns(table_info.name)
            for col_info in columns:
                col_result = await db.execute(
                    select(SchemaColumn).where(
                        SchemaColumn.schema_table_id == schema_table.id,
                        SchemaColumn.column_name == col_info.name,
                    )
                )
                schema_col = col_result.scalar_one_or_none()

                if not schema_col:
                    # Sample values
                    try:
                        samples = await connector.get_sample_values(
                            table_info.name, col_info.name, limit=10
                        )
                    except Exception:
                        samples = []

                    schema_col = SchemaColumn(
                        schema_table_id=schema_table.id,
                        column_name=col_info.name,
                        data_type=col_info.data_type,
                        is_nullable=col_info.is_nullable,
                        is_primary_key=col_info.is_primary_key,
                        is_foreign_key=col_info.is_foreign_key,
                        fk_references=col_info.fk_references,
                        ordinal_position=col_info.ordinal_position,
                        sample_values=samples,
                    )
                    db.add(schema_col)

        await db.flush()
        logger.info(f"Schema discovery complete for connection {connection_id}: {len(tables)} tables")
