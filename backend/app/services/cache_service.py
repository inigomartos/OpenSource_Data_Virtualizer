"""Redis query result caching."""

import json
from typing import Optional
import redis.asyncio as redis
from app.config import settings
from loguru import logger


class CacheService:
    """Redis-backed cache for query results."""

    def __init__(self, redis_url: str = None):
        self._redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Optional[dict]:
        """Get cached value by key."""
        try:
            client = await self._get_client()
            value = await client.get(f"datamind:cache:{key}")
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: dict, ttl_seconds: int = 300) -> None:
        """Set cached value with TTL."""
        try:
            client = await self._get_client()
            await client.setex(
                f"datamind:cache:{key}",
                ttl_seconds,
                json.dumps(value, default=str),
            )
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def delete(self, key: str) -> None:
        """Delete cached value."""
        try:
            client = await self._get_client()
            await client.delete(f"datamind:cache:{key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
