"""Alert management and checking."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
from app.models.alert_event import AlertEvent
from app.core.exceptions import NotFoundError


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(self, org_id: str, created_by_id: str, **kwargs) -> Alert:
        alert = Alert(org_id=org_id, created_by_id=created_by_id, **kwargs)
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def get_alerts(self, org_id: str) -> list[Alert]:
        result = await self.db.execute(
            select(Alert)
            .where(Alert.org_id == org_id)
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_event(self, alert_id: str, triggered_value: float, message: str) -> AlertEvent:
        event = AlertEvent(
            alert_id=alert_id,
            triggered_value=triggered_value,
            message=message,
        )
        self.db.add(event)
        await self.db.flush()
        return event
