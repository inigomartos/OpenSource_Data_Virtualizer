"""Connection CRUD endpoints.

All queries are scoped to the current user's organization for multi-tenancy.
Passwords are encrypted at rest using Fernet (AES-128-CBC) via
``app.core.security.encrypt_value``.  Password fields are **never** included
in API responses.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.database import get_db
from app.core.exceptions import raise_not_found
from app.core.security import encrypt_value
from app.dependencies import get_current_user, require_role
from app.models.connection import Connection
from app.models.user import User
from app.schemas.common import ListResponse
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResult,
)
from app.services.audit_service import AuditService
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

@router.get("/", response_model=ListResponse[ConnectionResponse])
async def list_connections(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all connections belonging to the caller's organization."""
    count_result = await db.execute(
        select(func.count()).select_from(Connection).where(Connection.org_id == user.org_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Connection)
        .where(Connection.org_id == user.org_id)
        .order_by(Connection.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    connections = result.scalars().all()
    return {"data": connections, "count": total}


@router.post("/", response_model=ConnectionResponse, status_code=201)
async def create_connection(
    payload: ConnectionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin", "analyst")),
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
    try:
        await AuditService.log(
            db=db, org_id=user.org_id, user_id=user.id,
            action="connection.create",
            resource_type="connection",
            resource_id=str(connection.id),
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Delete a connection from the caller's organization."""
    connection = await _get_connection_or_404(
        connection_id, user.org_id, db,
    )
    connection_id_str = str(connection.id)
    await db.delete(connection)
    await db.flush()
    try:
        await AuditService.log(
            db=db, org_id=user.org_id, user_id=user.id,
            action="connection.delete",
            resource_type="connection",
            resource_id=connection_id_str,
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails
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
            str(connection.id), str(user.org_id), db,
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
