"""Audit logging service for tracking user actions."""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Centralized audit logging for security and compliance tracking."""

    @staticmethod
    async def log(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            db: Async database session.
            org_id: Organization ID the action belongs to.
            user_id: User who performed the action.
            action: Action name (e.g. 'connection.create', 'query.execute').
            resource_type: Type of resource affected (e.g. 'connection', 'dashboard').
            resource_id: ID of the affected resource.
            details: Additional metadata about the action.
            ip_address: Client IP address.

        Returns:
            The created AuditLog entry.
        """
        entry = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(entry)
        await db.flush()
        return entry
