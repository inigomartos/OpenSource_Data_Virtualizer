"""Custom middleware: request logging, rate limiting."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.1f}ms)"
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting. For production, use Redis."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = {}  # ip -> [timestamps]

    async def dispatch(self, request: Request, call_next):
        # Get client IP (prefer X-Forwarded-For for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        now = time.time()
        window = 60  # 1 minute window

        # Periodic pruning: remove stale IPs when map grows too large
        if len(self.requests) > 1000:
            stale_ips = [
                ip for ip, timestamps in self.requests.items()
                if not timestamps or now - timestamps[-1] >= window
            ]
            for ip in stale_ips:
                del self.requests[ip]

        # Clean old entries and check rate
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < window
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(window)},
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response
