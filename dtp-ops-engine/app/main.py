import asyncio
import structlog
from app.workers.billing_worker import run_worker
from app.core.config import settings

logger = structlog.get_logger()

if __name__ == "__main__":
    logger.info("ops_worker_starting")
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("ops_worker_stopped")