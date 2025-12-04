import redis.asyncio as redis
import hashlib
import json
from typing import Optional, Any
import structlog

logger = structlog.get_logger()

# Singleton Redis Client
redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

class CacheService:
    @staticmethod
    def generate_key(prefix: str, *args) -> str:
        """Generates a consistent hash key based on inputs."""
        raw = f"{prefix}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(raw.encode()).hexdigest()

    @staticmethod
    async def get_rag_context(query: str, agent_id: str) -> Optional[str]:
        """
        Check if we already retrieved context for this exact query recently.
        """
        key = CacheService.generate_key("rag", agent_id, query.strip().lower())
        return await redis_client.get(key)

    @staticmethod
    async def set_rag_context(query: str, agent_id: str, context: str, ttl: int = 3600):
        """
        Cache context for 1 hour. 
        """
        key = CacheService.generate_key("rag", agent_id, query.strip().lower())
        await redis_client.set(key, context, ex=ttl)