"""Dashboard and widget management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dashboard import Dashboard
from app.models.widget import Widget
from app.core.exceptions import NotFoundError


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dashboard(self, org_id: str, created_by_id: str, title: str, description: str = None) -> Dashboard:
        dashboard = Dashboard(
            org_id=org_id,
            created_by_id=created_by_id,
            title=title,
            description=description,
        )
        self.db.add(dashboard)
        await self.db.flush()
        return dashboard

    async def get_dashboards(self, org_id: str) -> list[Dashboard]:
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.org_id == org_id)
            .order_by(Dashboard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_dashboard(self, dashboard_id: str, org_id: str) -> Dashboard:
        result = await self.db.execute(
            select(Dashboard).where(
                Dashboard.id == dashboard_id,
                Dashboard.org_id == org_id,
            )
        )
        dashboard = result.scalar_one_or_none()
        if not dashboard:
            raise NotFoundError("Dashboard not found")
        return dashboard

    async def add_widget(self, dashboard_id: str, **kwargs) -> Widget:
        widget = Widget(dashboard_id=dashboard_id, **kwargs)
        self.db.add(widget)
        await self.db.flush()
        return widget

    async def get_widgets(self, dashboard_id: str) -> list[Widget]:
        result = await self.db.execute(
            select(Widget).where(Widget.dashboard_id == dashboard_id)
        )
        return list(result.scalars().all())

    async def delete_dashboard(self, dashboard_id: str, org_id: str) -> None:
        dashboard = await self.get_dashboard(dashboard_id, org_id)
        await self.db.delete(dashboard)
