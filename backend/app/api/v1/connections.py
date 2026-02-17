"""Connection CRUD endpoints.

All queries are scoped to the current user's organization for multi-tenancy.
Passwords are encrypted at rest using Fernet (AES-128-CBC) via
``app.core.security.encrypt_value``.  Password fields are **never** included
in API responses.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import raise_not_found
from app.core.security import encrypt_value
from app.dependencies import get_current_user
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResult,
)
from app.services.connection_manager import ConnectionManager

router = APIRouter()
connection_manager = ConnectionManager()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_connection_or_404(
    connection_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> Connection:
    """Fetch a connection scoped to *org_id* or raise 404."""
    result = await db.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.org_id == org_id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise_not_found("Connection")
    return connection


# ── CRUD Endpoints ───────────────────────────────────────────────────────────

@router.get("/", response_model=list[ConnectionResponse])
async def list_connections(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all connections belonging to the caller's organization."""
    result = await db.execute(
        select(Connection)
        .where(Connection.org_id == user.org_id)
        .order_by(Connection.created_at.desc())
    )
    connections = result.scalars().all()
    return connections


@router.post("/", response_model=ConnectionResponse, status_code=201)
async def create_connection(
    payload: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new data connection.

    The plaintext password is encrypted before storage and is never returned
    in API responses.
    """
    password_encrypted = None
    if payload.password:
        password_encrypted = encrypt_value(payload.password)

    connection = Connection(
        org_id=user.org_id,
        created_by_id=user.id,
        name=payload.name,
        type=payload.type,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        password_encrypted=password_encrypted,
        ssl_mode=payload.ssl_mode,
        file_path=payload.file_path,
        is_active=True,
    )
    db.add(connection)
    await db.flush()
    await db.refresh(connection)
    return connection


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return a single connection (password fields are excluded by schema)."""
    connection = await _get_connection_or_404(
        connection_id, user.org_id, db,
    )
    return connection


@router.delete("/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a connection from the caller's organization."""
    connection = await _get_connection_or_404(
        connection_id, user.org_id, db,
    )
    await db.delete(connection)
    await db.flush()
    return None


# ── Test Connection ──────────────────────────────────────────────────────────

@router.post("/{connection_id}/test", response_model=ConnectionTestResult)
async def test_connection(
    connection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Test whether the stored credentials can reach the target database.

    Uses the connector factory to instantiate the appropriate driver and
    runs a lightweight connectivity check.
    """
    connection = await _get_connection_or_404(
        connection_id, user.org_id, db,
    )

    connector = None
    try:
        connector = await connection_manager.get_connector(
            str(connection.id), db,
        )
        success = await connector.test_connection()

        tables_found = None
        if success:
            try:
                tables = await connector.get_tables()
                tables_found = len(tables)
            except Exception:
                pass

        return ConnectionTestResult(
            success=success,
            message="Connection successful" if success else "Connection failed",
            tables_found=tables_found,
        )
    except Exception as exc:
        return ConnectionTestResult(
            success=False,
            message=f"Connection failed: {exc}",
        )
    finally:
        if connector is not None:
            try:
                await connector.close()
            except Exception:
                pass
