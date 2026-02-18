"""Alert CRUD endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import raise_not_found, raise_forbidden
from app.core.sql_validator import SQLSafetyValidator
from app.dependencies import get_current_user
from app.models.alert import Alert
from app.models.alert_event import AlertEvent
from app.models.connection import Connection
from app.models.user import User
from app.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertWithEvents,
    AlertEventResponse,
)
from app.schemas.common import ListResponse

router = APIRouter()
sql_validator = SQLSafetyValidator()


@router.get("/events/unread", response_model=ListResponse[AlertEventResponse])
async def get_unread_events(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all unread alert events for the user's organization (notification bell)."""
    result = await db.execute(
        select(AlertEvent)
        .join(Alert, AlertEvent.alert_id == Alert.id)
        .where(Alert.org_id == user.org_id, AlertEvent.is_read == False)
        .order_by(AlertEvent.created_at.desc())
        .limit(50)
    )
    events = result.scalars().all()
    return {"data": events, "count": len(events)}


@router.post("/events/read-all", status_code=200)
async def mark_all_events_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AlertEvent)
        .join(Alert, AlertEvent.alert_id == Alert.id)
        .where(Alert.org_id == user.org_id, AlertEvent.is_read == False)
    )
    events = result.scalars().all()
    for event in events:
        event.is_read = True
    await db.flush()
    return {"marked_read": len(events)}


@router.get("/", response_model=ListResponse[AlertResponse])
async def list_alerts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all alerts for the user's organization."""
    count_result = await db.execute(
        select(func.count()).select_from(Alert).where(Alert.org_id == user.org_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Alert)
        .where(Alert.org_id == user.org_id)
        .order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    alerts = result.scalars().all()
    return {"data": alerts, "count": total}


@router.post("/", status_code=201, response_model=AlertResponse)
async def create_alert(
    payload: AlertCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new alert with SQL validation."""
    # Validate the SQL query
    validation = sql_validator.validate(payload.query_sql)
    if not validation["is_safe"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL validation failed: {validation['reason']}",
        )

    # Verify the connection belongs to the user's org
    conn_result = await db.execute(
        select(Connection).where(
            Connection.id == payload.connection_id,
            Connection.org_id == user.org_id,
        )
    )
    connection = conn_result.scalar_one_or_none()
    if not connection:
        raise_not_found("Connection")

    alert = Alert(
        org_id=user.org_id,
        created_by_id=user.id,
        connection_id=payload.connection_id,
        name=payload.name,
        description=payload.description,
        query_sql=validation.get("parsed_sql", payload.query_sql),
        condition_type=payload.condition_type,
        threshold_value=payload.threshold_value,
        check_interval_minutes=payload.check_interval_minutes,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.get("/{alert_id}", response_model=AlertWithEvents)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single alert with its recent events."""
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.events))
        .where(Alert.id == alert_id, Alert.org_id == user.org_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise_not_found("Alert")

    # Sort events by created_at desc and limit to recent 20
    alert.events = sorted(alert.events, key=lambda e: e.created_at, reverse=True)[:20]
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an existing alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.org_id == user.org_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise_not_found("Alert")

    update_data = payload.model_dump(exclude_unset=True)

    # If query_sql is being updated, validate it
    if "query_sql" in update_data and update_data["query_sql"] is not None:
        validation = sql_validator.validate(update_data["query_sql"])
        if not validation["is_safe"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SQL validation failed: {validation['reason']}",
            )
        update_data["query_sql"] = validation.get("parsed_sql", update_data["query_sql"])

    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.flush()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.org_id == user.org_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise_not_found("Alert")

    await db.delete(alert)
    await db.flush()
    return None


@router.get("/{alert_id}/events", response_model=ListResponse[AlertEventResponse])
async def get_alert_events(
    alert_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get paginated alert events for a specific alert."""
    # Verify alert belongs to org
    alert_result = await db.execute(
        select(Alert.id).where(Alert.id == alert_id, Alert.org_id == user.org_id)
    )
    if not alert_result.scalar_one_or_none():
        raise_not_found("Alert")

    result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.alert_id == alert_id)
        .order_by(AlertEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    events = result.scalars().all()
    return {"data": events, "count": len(events)}


@router.post("/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Toggle an alert's is_active status."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.org_id == user.org_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise_not_found("Alert")

    alert.is_active = not alert.is_active
    await db.flush()
    await db.refresh(alert)
    return alert


@router.post("/events/{event_id}/read", response_model=AlertEventResponse)
async def mark_event_read(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark an alert event as read."""
    result = await db.execute(
        select(AlertEvent)
        .join(Alert, AlertEvent.alert_id == Alert.id)
        .where(AlertEvent.id == event_id, Alert.org_id == user.org_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise_not_found("Alert event")

    event.is_read = True
    await db.flush()
    await db.refresh(event)
    return event
