import asyncio
import structlog

logger = structlog.get_logger()

async def send_welcome_email(email: str, tenant_name: str):
    """
    Simulates sending an email via SendGrid/AWS SES.
    This runs in the background.
    """
    await asyncio.sleep(1) # Simulate network delay
    logger.info("email_sent", recipient=email, type="welcome_tenant")