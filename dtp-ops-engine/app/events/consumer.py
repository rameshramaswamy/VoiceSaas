import redis.asyncio as redis
import json
import asyncio
import structlog

logger = structlog.get_logger()

class EventConsumer:
    def __init__(self, redis_url: str, group_name: str, consumer_name: str):
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.stream_key = "dtp_events"
        self.group = group_name
        self.consumer = consumer_name

    async def setup(self):
        """Ensure Consumer Group exists"""
        try:
            # Create group, start from beginning (0)
            await self.redis.xgroup_create(self.stream_key, self.group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise e

    async def consume(self, handler_callback):
        """Infinite loop to process messages"""
        while True:
            try:
                # Read new messages for this group
                # '>' means "give me messages never delivered to this consumer"
                streams = await self.redis.xreadgroup(
                    self.group, self.consumer, {self.stream_key: ">"}, count=10, block=2000
                )

                if not streams:
                    await asyncio.sleep(0.1)
                    continue

                for stream_name, messages in streams:
                    for message_id, data in messages:
                        event_type = data.get("type")
                        payload = json.loads(data.get("payload", "{}"))
                        
                        logger.info("processing_event", id=message_id, type=event_type)
                        
                        # Process logic
                        await handler_callback(event_type, payload)
                        
                        # Acknowledge (mark as processed)
                        await self.redis.xack(self.stream_key, self.group, message_id)

            except Exception as e:
                logger.error("consumer_error", error=str(e))
                await asyncio.sleep(1)