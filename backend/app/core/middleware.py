"""Custom middleware: request logging, Redis-backed rate limiting."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from loguru import logger

import redis.asyncio as aioredis


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)"
        )
        return response


# Per-endpoint rate limits (requests per minute)
ENDPOINT_RATE_LIMITS: dict[str, int] = {
    "/api/v1/auth/login": 5,
    "/api/v1/auth/register": 5,
    "/api/v1/chat/message": 20,
}
DEFAULT_RATE_LIMIT = 100


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiting with per-endpoint limits.

    Falls back to allowing requests if Redis is unreachable (fail-open)
    to avoid blocking all traffic on Redis outage.
    """

    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is None:
            try:
                from app.config import settings
                url = self._redis_url or settings.REDIS_URL
                self._redis = aioredis.from_url(url, decode_responses=True)
                await self._redis.ping()
            except Exception as e:
                logger.warning(f"Rate limiter: Redis connection failed: {e}")
                self._redis = None
        return self._redis

    def _get_rate_limit(self, path: str) -> int:
        """Get the rate limit for a given endpoint path."""
        for endpoint, limit in ENDPOINT_RATE_LIMITS.items():
            if path.startswith(endpoint):
                return limit
        return DEFAULT_RATE_LIMIT

    def _get_bucket(self, path: str) -> str:
        """Get the rate limit bucket name for grouping."""
        for endpoint in ENDPOINT_RATE_LIMITS:
            if path.startswith(endpoint):
                return endpoint
        return "default"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Check if rate limiting is enabled
        try:
            from app.config import settings
            if hasattr(settings, "RATE_LIMIT_ENABLED") and not settings.RATE_LIMIT_ENABLED:
                return await call_next(request)
        except Exception:
            pass

        # Get client IP (prefer X-Real-IP set by nginx, then X-Forwarded-For)
        client_ip = request.headers.get("X-Real-IP")
        if not client_ip:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"

        path = request.url.path
        rate_limit = self._get_rate_limit(path)
        bucket = self._get_bucket(path)
        redis_key = f"ratelimit:{client_ip}:{bucket}"
        window = 60  # 1 minute

        try:
            redis_client = await self._get_redis()
            if redis_client is None:
                # Fail-open: allow request if Redis is down
                return await call_next(request)

            # Atomic INCR + conditional EXPIRE via pipeline
            pipe = redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            results = await pipe.execute()

            current_count = results[0]
            ttl = results[1]

            # Set TTL only on first request (when key was just created)
            if ttl == -1:
                await redis_client.expire(redis_key, window)

            if current_count > rate_limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={
                        "Retry-After": str(window),
                        "X-RateLimit-Limit": str(rate_limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit - current_count))
            return response

        except Exception as e:
            # Fail-open: any Redis error should not block requests
            logger.warning(f"Rate limiter error (allowing request): {e}")
            return await call_next(request)
