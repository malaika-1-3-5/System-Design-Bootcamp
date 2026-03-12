"""Rate limiter middleware using Redis sliding window."""

import time
import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import get_gateway_settings

settings = get_gateway_settings()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter."""

    def __init__(self, app):
        super().__init__(app)
        self.redis = None
        self.limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # seconds

    async def _get_redis(self):
        if self.redis is None:
            try:
                self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                return None
        return self.redis

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health & docs
        if request.url.path in ("/api/v1/health", "/docs", "/openapi.json", "/"):
            return await call_next(request)

        r = await self._get_redis()
        if r is None:
            # If Redis is unavailable, allow through
            return await call_next(request)

        # Identify client by IP or JWT subject
        client_id = request.client.host or "unknown"
        print(f"client_id: {client_id}")
        key = f"rate:{client_id}:{int(time.time()) // self.window}"

        try:
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, self.window)

            if current > self.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "limit": self.limit,
                        "window_seconds": self.window,
                    },
                )
        except Exception:
            pass  # Fail open if Redis errors

        response = await call_next(request)
        return response
