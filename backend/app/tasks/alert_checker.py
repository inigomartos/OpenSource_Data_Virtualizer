"""Celery task: periodic alert checking."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app
from app.core.database import async_session_factory
from app.core.sql_validator import SQLSafetyValidator
from app.models.alert import Alert
from app.models.alert_event import AlertEvent
from app.models.connection import Connection
from app.services.connection_manager import ConnectionManager
from loguru import logger

sql_validator = SQLSafetyValidator()
connection_manager = ConnectionManager()


async def _check_single_alert(alert: Alert, db: AsyncSession) -> None:
    """Check a single alert: execute SQL, compare to threshold, create event if triggered."""
    now = datetime.now(timezone.utc)

    try:
        # Validate SQL before execution
        validation = sql_validator.validate(alert.query_sql)
        if not validation["is_safe"]:
            logger.warning(
                f"Alert {alert.id} ({alert.name}) has invalid SQL: {validation['reason']}"
            )
            alert.consecutive_failures += 1
            alert.last_checked_at = now
            return

        # Get connector for the alert's connection
        connector = await connection_manager.get_connector_internal(str(alert.connection_id), db)

        try:
            # Execute the alert's query
            result = await connector.execute_query(
                sql=validation.get("parsed_sql", alert.query_sql),
                timeout=30,
                max_rows=1,
            )

            if result.error:
                logger.error(
                    f"Alert {alert.id} ({alert.name}) query error: {result.error}"
                )
                alert.consecutive_failures += 1
                alert.last_checked_at = now
                return

            # Extract the first numeric value from results
            value = _extract_numeric_value(result.rows)
            if value is None:
                logger.warning(
                    f"Alert {alert.id} ({alert.name}): no numeric value in query result"
                )
                alert.consecutive_failures += 1
                alert.last_checked_at = now
                return

            # Compare against threshold
            triggered = _evaluate_condition(
                condition_type=alert.condition_type,
                value=value,
                threshold=alert.threshold_value,
                last_value=alert.last_value,
            )

            if triggered:
                message = _build_trigger_message(
                    alert_name=alert.name,
                    condition_type=alert.condition_type,
                    value=value,
                    threshold=alert.threshold_value,
                    last_value=alert.last_value,
                )
                event = AlertEvent(
                    alert_id=alert.id,
                    triggered_value=value,
                    message=message,
                )
                db.add(event)
                logger.info(f"Alert {alert.id} ({alert.name}) TRIGGERED: {message}")

            # Update alert state
            alert.last_value = value
            alert.last_checked_at = now
            alert.consecutive_failures = 0

        finally:
            await connector.close()

    except Exception as e:
        logger.error(f"Alert {alert.id} ({alert.name}) check failed: {e}")
        alert.consecutive_failures += 1
        alert.last_checked_at = now


def _extract_numeric_value(rows: list[list]) -> Decimal | None:
    """Extract the first numeric value from query result rows."""
    if not rows or not rows[0]:
        return None

    for cell in rows[0]:
        if cell is None:
            continue
        try:
            return Decimal(str(cell))
        except (InvalidOperation, ValueError, TypeError):
            continue

    return None


def _evaluate_condition(
    condition_type: str,
    value: Decimal,
    threshold: Decimal | None,
    last_value: Decimal | None,
) -> bool:
    """Evaluate whether the alert condition is triggered."""
    if threshold is None and condition_type != "anomaly":
        return False

    if condition_type == "above":
        return value > threshold

    elif condition_type == "below":
        return value < threshold

    elif condition_type == "change_pct":
        if last_value is None or last_value == 0:
            return False
        pct_change = abs((value - last_value) / last_value) * 100
        return pct_change > threshold

    elif condition_type == "anomaly":
        # Placeholder: anomaly detection not yet implemented
        return False

    return False


def _build_trigger_message(
    alert_name: str,
    condition_type: str,
    value: Decimal,
    threshold: Decimal | None,
    last_value: Decimal | None,
) -> str:
    """Build a human-readable trigger message."""
    if condition_type == "above":
        return (
            f"Alert '{alert_name}' triggered: value {value} is above "
            f"threshold {threshold}"
        )
    elif condition_type == "below":
        return (
            f"Alert '{alert_name}' triggered: value {value} is below "
            f"threshold {threshold}"
        )
    elif condition_type == "change_pct":
        if last_value and last_value != 0:
            pct = abs((value - last_value) / last_value) * 100
            return (
                f"Alert '{alert_name}' triggered: value changed from {last_value} "
                f"to {value} ({pct:.1f}% change, threshold {threshold}%)"
            )
        return f"Alert '{alert_name}' triggered: value {value} (percentage change exceeded threshold)"
    elif condition_type == "anomaly":
        return f"Alert '{alert_name}' triggered: anomaly detected, value {value}"

    return f"Alert '{alert_name}' triggered: value {value}"


async def _run_alert_check_cycle() -> None:
    """Main async logic: query all active alerts and check each one."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Alert).where(Alert.is_active == True)
            )
            alerts = result.scalars().all()

            if not alerts:
                logger.debug("No active alerts to check")
                return

            logger.info(f"Checking {len(alerts)} active alerts")

            for alert in alerts:
                await _check_single_alert(alert, db)

            await db.commit()
            logger.info(f"Alert check cycle complete: {len(alerts)} alerts processed")

        except Exception as e:
            await db.rollback()
            logger.error(f"Alert check cycle failed: {e}")
            raise


@celery_app.task(name="app.tasks.alert_checker.check_alerts")
def check_alerts():
    """Check all active alerts against their SQL conditions."""
    logger.info("Running alert check cycle...")
    asyncio.run(_run_alert_check_cycle())
    logger.info("Alert check cycle complete")
