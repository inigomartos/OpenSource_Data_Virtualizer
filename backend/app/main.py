"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.api.websocket import websocket_router
from app.core.database import engine
from app.core.middleware import RequestLoggingMiddleware
from app.config import settings
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DataMind API...")
    yield
    logger.info("Shutting down DataMind API...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="DataMind API",
        version="1.0.0",
        description="AI-powered business intelligence platform",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(websocket_router)

    return app


app = create_app()
