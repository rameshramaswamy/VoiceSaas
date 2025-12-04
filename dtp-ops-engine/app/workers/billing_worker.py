from app.events.consumer import EventConsumer
from app.billing.service import BillingService
from app.core.config import settings

billing_service = BillingService()

async def handle_event(event_type: str, payload: dict):
    if event_type == "call.ended":
        await billing_service.process_call_cost(payload)
    # Add other event types here (e.g., "sms.sent")

async def run_worker():
    consumer = EventConsumer(
        redis_url=settings.REDIS_URL,
        group_name="billing_group",
        consumer_name="worker_1"
    )
    await consumer.setup()
    await consumer.consume(handle_event)