"""Main API router aggregating all sub-routers."""

from fastapi import APIRouter
from app.api.v1 import auth, health, connections, chat, dashboards, alerts, export, upload, schema, query, audit, org

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(connections.router, prefix="/connections", tags=["Connections"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(schema.router, prefix="/schema", tags=["Schema"])
api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(org.router, prefix="/org", tags=["Organization"])
