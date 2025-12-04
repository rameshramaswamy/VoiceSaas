from sqlalchemy.sql import text
from app.db.session import async_session
from app.billing.pricing import Pricing
import structlog

logger = structlog.get_logger()

class BillingService:
    async def process_call_cost(self, payload: dict):
        """
        Calculates total cost and updates Tenant balance.
        Payload expects: {
            "tenant_id": uuid,
            "duration_sec": int,
            "prompt_tokens": int,
            "completion_tokens": int,
            "tts_chars": int
        }
        """
        tenant_id = payload.get("tenant_id")
        if not tenant_id: return

        # 1. Calculate Cost
        stt_cost = (payload.get("duration_sec", 0) / 60) * Pricing.STT_PER_MIN
        llm_cost = (payload.get("prompt_tokens", 0) * Pricing.LLM_IN_TOKEN) + \
                   (payload.get("completion_tokens", 0) * Pricing.LLM_OUT_TOKEN)
        tts_cost = payload.get("tts_chars", 0) * Pricing.TTS_PER_CHAR
        
        total_cost = stt_cost + llm_cost + tts_cost + Pricing.PLATFORM_FEE_PER_CALL
        
        # 2. Database Transaction (Deduct Credits)
        # Assuming we have a 'tenants' table with 'credits_balance'
        async with async_session() as session:
            async with session.begin():
                # Check idempotency here (if call_id already billed) - skipped for brevity
                
                # Update Balance
                await session.execute(
                    text("""
                        UPDATE tenants 
                        SET credits_balance = credits_balance - :cost 
                        WHERE id = :id
                    """),
                    {"cost": total_cost, "id": tenant_id}
                )
                
                # Log Transaction
                await session.execute(
                    text("""
                        INSERT INTO billing_logs (tenant_id, amount, description, created_at)
                        VALUES (:tid, :amt, 'Voice Call Usage', NOW())
                    """),
                    {"tid": tenant_id, "amt": -total_cost}
                )
                
        logger.info("billing_processed", tenant_id=tenant_id, cost=total_cost)