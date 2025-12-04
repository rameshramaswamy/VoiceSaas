import redis.asyncio as redis
import json
import structlog
from datetime import datetime

logger = structlog.get_logger()

class EventProducer:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.stream_key = "dtp_events"

    async def publish(self, event_type: str, payload: dict):
        """
        Publishes an event to the stream.
        event_type: 'call.ended', 'tool.used'
        """
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": json.dumps(payload)
        }
        try:
            # XADD adds to the stream
            await self.redis.xadd(self.stream_key, message)
            logger.debug("event_published", type=event_type)
        except Exception as e:
            logger.error("publish_failed", error=str(e))