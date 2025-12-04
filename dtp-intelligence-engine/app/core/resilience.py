from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import structlog
import logging
import openai
import pinecone

logger = structlog.get_logger()

# Retry configuration for External APIs (OpenAI, Pinecone)
# Wait 2^x * 1 second between retries, up to 3 times.
external_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        openai.APIConnectionError, 
        openai.RateLimitError,
        pinecone.core.client.exceptions.ServiceException
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)

# Tool execution timeout (Circuit Breaker logic would go here in full mesh)
# For now, we rely on timeout arguments in the http clients.