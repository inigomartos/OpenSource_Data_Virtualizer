"""Manages database connection pools using read-only credentials."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connection import Connection
from app.core.security import decrypt_value
from app.core.exceptions import NotFoundError, ConnectionError as ConnError
from app.connectors.base import BaseConnector
from app.connectors.postgres import PostgreSQLConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.sqlite import SQLiteConnector
from loguru import logger


class ConnectionManager:
    """Creates and manages database connectors with read-only credentials."""

    async def get_connector(self, connection_id: str, db: AsyncSession) -> BaseConnector:
        """Get a connector for the specified connection, using read-only credentials."""
        result = await db.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        conn = result.scalar_one_or_none()

        if not conn:
            raise NotFoundError(f"Connection {connection_id} not found")

        if not conn.is_active:
            raise ConnError(f"Connection {conn.name} is inactive")

        # SECURITY: Use readonly credentials, NEVER the admin credentials
        username = conn.readonly_username or conn.username
        password = None
        try:
            encrypted_pw = conn.readonly_password_encrypted or conn.password_encrypted
            if encrypted_pw:
                password = decrypt_value(encrypted_pw)
        except Exception as e:
            logger.error(f"Failed to decrypt connection password: {e}")
            raise ConnError("Failed to decrypt connection credentials")

        return self._create_connector(
            conn_type=conn.type,
            host=conn.host,
            port=conn.port,
            database=conn.database_name,
            username=username,
            password=password,
            file_path=conn.file_path,
            ssl_mode=conn.ssl_mode,
        )

    def _create_connector(
        self,
        conn_type: str,
        host: str = None,
        port: int = None,
        database: str = None,
        username: str = None,
        password: str = None,
        file_path: str = None,
        ssl_mode: str = "prefer",
    ) -> BaseConnector:
        """Factory method to create the appropriate connector."""
        if conn_type == "postgresql":
            return PostgreSQLConnector(
                host=host, port=port or 5432, database=database,
                username=username, password=password, ssl_mode=ssl_mode,
            )
        elif conn_type == "mysql":
            return MySQLConnector(
                host=host, port=port or 3306, database=database,
                username=username, password=password,
            )
        elif conn_type == "sqlite":
            return SQLiteConnector(file_path=file_path or database)
        else:
            raise ConnError(f"Unsupported connection type: {conn_type}")
