"""Celery task: scheduled report generation."""

from app.tasks.celery_app import celery_app
from loguru import logger


@celery_app.task(name="app.tasks.report_generator.generate_scheduled_report")
def generate_scheduled_report(dashboard_id: str, format: str = "pdf"):
    """Generate and email a scheduled dashboard report."""
    logger.info(f"Generating {format} report for dashboard {dashboard_id}...")
    # TODO: Implement report generation
    logger.info(f"Report generation complete for dashboard {dashboard_id}")
