"""Audit log endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import raise_forbidden
from app.dependencies import get_current_user, require_role
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[uuid.UUID] = None
    details: dict
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuditResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    offset: int
    limit: int


@router.get("/", response_model=PaginatedAuditResponse)
async def list_audit_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    action: Optional[str] = Query(default=None, description="Filter by action name"),
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type"),
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs for the organization (admin only, paginated)."""
    # Base query scoped to org
    base_query = select(AuditLog).where(AuditLog.org_id == user.org_id)

    # Optional filters
    if action:
        base_query = base_query.where(AuditLog.action == action)
    if resource_type:
        base_query = base_query.where(AuditLog.resource_type == resource_type)

    # Count total matching records
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    result = await db.execute(
        base_query
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()

    return PaginatedAuditResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )
