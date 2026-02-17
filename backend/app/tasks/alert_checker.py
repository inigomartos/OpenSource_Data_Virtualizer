"""Celery task: periodic alert checking."""

from app.tasks.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.tasks.alert_checker.check_alerts")
def check_alerts():
    """Check all active alerts against their SQL conditions."""
    logger.info("Running alert check cycle...")
    # TODO: Implement alert checking logic
    # 1. Query all active alerts
    # 2. Execute each alert's SQL
    # 3. Compare result to threshold
    # 4. Create alert_event if triggered
    # 5. Track consecutive_failures
    logger.info("Alert check cycle complete")
