"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from app.api.router import api_router
from app.api.websocket import websocket_router, ws_manager
from app.core.database import engine
from app.core.middleware import RequestIDMiddleware, RequestLoggingMiddleware, RateLimitMiddleware
from app.core.logging_config import configure_logging
from app.core.exceptions import DataMindException, AuthenticationError, AuthorizationError, NotFoundError
from app.config import settings
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DataMind API...")
    await ws_manager.initialize()
    yield
    logger.info("Shutting down DataMind API...")
    await ws_manager.shutdown()
    await engine.dispose()


configure_logging(debug=settings.DEBUG)

# Initialize Sentry (no-op if DSN is empty)
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment="development" if settings.DEBUG else "production",
    )
    logger.info("Sentry initialized")


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
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(websocket_router)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.message})

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(DataMindException)
    async def datamind_error_handler(request, exc: DataMindException):
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


app = create_app()
