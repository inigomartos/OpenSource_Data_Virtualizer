"""Health check endpoint with DB and Redis connectivity verification."""

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.config import settings
from app.core.database import engine

router = APIRouter()


@router.get("/health")
async def health_check(detail: bool = Query(default=False)):
    """Return service health status.

    Checks PostgreSQL and Redis connectivity. Returns ``healthy`` when
    both are reachable, ``degraded`` when at least one is down, and
    ``unhealthy`` when all are down.  Pass ``?detail=true`` to see
    per-check results.
    """
    checks: dict[str, bool] = {}

    # ── PostgreSQL ──────────────────────────────────────────────────
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # ── Redis ───────────────────────────────────────────────────────
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    # ── Status ──────────────────────────────────────────────────────
    all_ok = all(checks.values())
    any_ok = any(checks.values())

    if all_ok:
        status = "healthy"
    elif any_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    response = {
        "status": status,
        "service": "datamind-api",
        "version": "1.0.0",
    }

    if detail:
        response["checks"] = checks

    return response
