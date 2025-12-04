import redis.asyncio as redis
import orjson
from typing import Optional, Any
from app.core.config import settings

# Initialize Redis Pool
redis_client = redis.from_url(
    "redis://localhost:6379", # In prod, use settings.REDIS_URL
    encoding="utf-8", 
    decode_responses=True
)

class CacheService:
    @staticmethod
    async def get(key: str) -> Optional[dict]:
        """Get value from Redis and deserialize."""
        value = await redis_client.get(key)
        if value:
            return orjson.loads(value)
        return None

    @staticmethod
    async def set(key: str, value: Any, expire: int = 3600):
        """Serialize value and store in Redis with TTL."""
        # Use ORJSON for speed
        json_val = orjson.dumps(value).decode('utf-8')
        await redis_client.set(key, json_val, ex=expire)

    @staticmethod
    async def delete(key: str):
        await redis_client.delete(key)
        
    @staticmethod
    async def invalidate_pattern(pattern: str):
        """Bulk delete keys (use carefully in prod)"""
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)