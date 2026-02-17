"""Dashboard and Widget CRUD endpoints.

All dashboard queries are scoped to the current user's organization for
multi-tenancy isolation.  Widget operations first verify that the parent
dashboard belongs to the caller's org.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from app.core.database import get_db
from app.core.exceptions import raise_not_found, raise_forbidden
from app.core.sql_validator import SQLSafetyValidator
from app.dependencies import get_current_user
from app.models.connection import Connection
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.common import ListResponse
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardWithWidgets,
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetRefreshResponse,
    PinFromChatRequest,
)
from app.services.audit_service import AuditService
from app.services.connection_manager import ConnectionManager

router = APIRouter()
connection_manager = ConnectionManager()
sql_validator = SQLSafetyValidator()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_dashboard_or_404(
    dashboard_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession,
    *,
    load_widgets: bool = False,
) -> Dashboard:
    """Fetch a dashboard scoped to *org_id* or raise 404."""
    stmt = select(Dashboard).where(
        Dashboard.id == dashboard_id,
        Dashboard.org_id == org_id,
    )
    if load_widgets:
        stmt = stmt.options(selectinload(Dashboard.widgets))
    result = await db.execute(stmt)
    dashboard = result.scalar_one_or_none()
    if not dashboard:
        raise_not_found("Dashboard")
    return dashboard


async def _get_widget_or_404(
    widget_id: uuid.UUID,
    dashboard_id: uuid.UUID,
    db: AsyncSession,
) -> Widget:
    """Fetch a widget that belongs to the given dashboard or raise 404."""
    result = await db.execute(
        select(Widget).where(
            Widget.id == widget_id,
            Widget.dashboard_id == dashboard_id,
        )
    )
    widget = result.scalar_one_or_none()
    if not widget:
        raise_not_found("Widget")
    return widget


# ── Dashboard CRUD ───────────────────────────────────────────────────────────

@router.get("/", response_model=ListResponse[DashboardResponse])
async def list_dashboards(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all dashboards belonging to the caller's organization."""
    widget_count_sq = (
        select(func.count(Widget.id))
        .where(Widget.dashboard_id == Dashboard.id)
        .correlate(Dashboard)
        .scalar_subquery()
        .label("widget_count")
    )
    result = await db.execute(
        select(Dashboard, widget_count_sq)
        .where(Dashboard.org_id == user.org_id)
        .order_by(Dashboard.updated_at.desc())
    )
    rows = result.all()
    dashboards = []
    for dashboard, wc in rows:
        resp = DashboardResponse.model_validate(dashboard)
        resp.widget_count = wc or 0
        dashboards.append(resp)
    return {"data": dashboards, "count": len(dashboards)}


@router.post("/", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    payload: DashboardCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new dashboard for the caller's organization."""
    dashboard = Dashboard(
        org_id=user.org_id,
        created_by_id=user.id,
        title=payload.title,
        description=payload.description,
        is_shared=False,
        layout_config=[],
    )
    db.add(dashboard)
    await db.flush()
    await db.refresh(dashboard)
    try:
        await AuditService.log(
            db=db, org_id=user.org_id, user_id=user.id,
            action="dashboard.create",
            resource_type="dashboard",
            resource_id=str(dashboard.id),
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardWithWidgets)
async def get_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return a single dashboard with all its widgets."""
    dashboard = await _get_dashboard_or_404(
        dashboard_id, user.org_id, db, load_widgets=True,
    )
    return dashboard


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    payload: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a dashboard's mutable fields."""
    dashboard = await _get_dashboard_or_404(dashboard_id, user.org_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dashboard, field, value)

    await db.flush()
    await db.refresh(dashboard)
    return dashboard


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a dashboard and all of its widgets (cascade)."""
    dashboard = await _get_dashboard_or_404(dashboard_id, user.org_id, db)
    dashboard_id_str = str(dashboard.id)
    await db.delete(dashboard)
    await db.flush()
    try:
        await AuditService.log(
            db=db, org_id=user.org_id, user_id=user.id,
            action="dashboard.delete",
            resource_type="dashboard",
            resource_id=dashboard_id_str,
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails
    return None


# ── Widget CRUD ──────────────────────────────────────────────────────────────

@router.post(
    "/{dashboard_id}/widgets",
    response_model=WidgetResponse,
    status_code=201,
)
async def create_widget(
    dashboard_id: uuid.UUID,
    payload: WidgetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a new widget to a dashboard."""
    # Verify parent dashboard belongs to user's org
    await _get_dashboard_or_404(dashboard_id, user.org_id, db)

    # Validate SQL if provided
    if payload.query_sql:
        validation = sql_validator.validate(payload.query_sql)
        if not validation["is_safe"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SQL validation failed: {validation['reason']}")

    # Verify connection belongs to org
    if payload.connection_id:
        conn_result = await db.execute(
            select(Connection).where(Connection.id == payload.connection_id, Connection.org_id == user.org_id)
        )
        if not conn_result.scalar_one_or_none():
            raise_not_found("Connection")

    widget = Widget(
        dashboard_id=dashboard_id,
        connection_id=payload.connection_id,
        title=payload.title,
        widget_type=payload.widget_type,
        query_sql=payload.query_sql,
        chart_config=payload.chart_config,
        refresh_interval_seconds=payload.refresh_interval_seconds,
        position={},
    )
    db.add(widget)
    await db.flush()
    await db.refresh(widget)
    return widget


@router.put(
    "/{dashboard_id}/widgets/{widget_id}",
    response_model=WidgetResponse,
)
async def update_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    payload: WidgetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a widget's mutable fields."""
    await _get_dashboard_or_404(dashboard_id, user.org_id, db)
    widget = await _get_widget_or_404(widget_id, dashboard_id, db)

    update_data = payload.model_dump(exclude_unset=True)

    # Validate SQL if being updated
    if "query_sql" in update_data and update_data["query_sql"]:
        validation = sql_validator.validate(update_data["query_sql"])
        if not validation["is_safe"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SQL validation failed: {validation['reason']}")

    for field, value in update_data.items():
        setattr(widget, field, value)

    await db.flush()
    await db.refresh(widget)
    return widget


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def delete_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove a widget from a dashboard."""
    await _get_dashboard_or_404(dashboard_id, user.org_id, db)
    widget = await _get_widget_or_404(widget_id, dashboard_id, db)
    await db.delete(widget)
    await db.flush()
    return None


# ── Widget Refresh ───────────────────────────────────────────────────────────

@router.post(
    "/{dashboard_id}/widgets/{widget_id}/refresh",
    response_model=WidgetRefreshResponse,
)
async def refresh_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Re-execute the widget's SQL query and return fresh data."""
    await _get_dashboard_or_404(dashboard_id, user.org_id, db)
    widget = await _get_widget_or_404(widget_id, dashboard_id, db)

    if not widget.connection_id:
        return WidgetRefreshResponse(
            widget_id=widget.id,
            error="Widget has no associated connection",
        )

    # Validate SQL before executing
    if widget.query_sql:
        validation = sql_validator.validate(widget.query_sql)
        if not validation["is_safe"]:
            return WidgetRefreshResponse(widget_id=widget.id, error=f"Widget SQL is unsafe: {validation['reason']}")

    connector = None
    try:
        connector = await connection_manager.get_connector(
            str(widget.connection_id), str(user.org_id), db,
        )
        query_result = await connector.execute_query(widget.query_sql)

        widget.last_refreshed_at = datetime.now(timezone.utc)
        widget.last_error = query_result.error

        await db.flush()
        await db.refresh(widget)

        return WidgetRefreshResponse(
            widget_id=widget.id,
            query_result_preview={
                "columns": query_result.columns,
                "rows": query_result.rows,
                "row_count": query_result.row_count,
                "execution_time_ms": query_result.execution_time_ms,
            },
            last_refreshed_at=widget.last_refreshed_at,
            error=query_result.error,
        )
    except Exception as exc:
        widget.last_error = str(exc)
        widget.last_refreshed_at = datetime.now(timezone.utc)
        await db.flush()

        return WidgetRefreshResponse(
            widget_id=widget.id,
            error=str(exc),
            last_refreshed_at=widget.last_refreshed_at,
        )
    finally:
        if connector is not None:
            try:
                await connector.close()
            except Exception:
                pass


# ── Pin-from-Chat ────────────────────────────────────────────────────────────

@router.post("/pin-from-chat", response_model=WidgetResponse, status_code=201)
async def pin_from_chat(
    payload: PinFromChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a widget from a chat message (generated_sql + chart_config).

    The target dashboard must belong to the caller's org.  The chat message
    is looked up to extract *generated_sql* and *chart_config*.
    """
    # Verify target dashboard belongs to the user's org
    dashboard = await _get_dashboard_or_404(
        payload.dashboard_id, user.org_id, db,
    )

    # Fetch the chat message
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.id == payload.message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise_not_found("ChatMessage")

    # Verify the chat session that owns this message belongs to the user
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == message.session_id)
    )
    session = result.scalar_one_or_none()
    if not session or session.user_id != user.id:
        raise_forbidden("Cannot access this chat message")

    # Determine widget title
    title = payload.title or f"Pinned: {(message.content[:60] + '...') if len(message.content) > 60 else message.content}"

    widget = Widget(
        dashboard_id=dashboard.id,
        connection_id=session.connection_id,
        title=title,
        widget_type="chart" if message.chart_config else "table",
        query_sql=message.generated_sql or "",
        chart_config=message.chart_config or {},
        position={},
    )
    db.add(widget)
    await db.flush()
    await db.refresh(widget)
    return widget
