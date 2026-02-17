"""Celery application configuration."""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "datamind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.alert_checker", "app.tasks.schema_refresh", "app.tasks.report_generator"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-alerts": {
            "task": "app.tasks.alert_checker.check_alerts",
            "schedule": 60.0,  # Every minute
        },
        "refresh-schemas": {
            "task": "app.tasks.schema_refresh.refresh_all_schemas",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)
