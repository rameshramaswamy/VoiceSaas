from fastapi import APIRouter, Response
from sqlalchemy.sql import text
from app.db.session import AsyncSessionLocal
from app.core.cache import redis_client
import structlog

router = APIRouter()
logger = structlog.get_logger()

@router.get("/health/live")
async def liveness_probe():
    """K8s Liveness: Is the app process running?"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe(response: Response):
    """
    K8s Readiness: Can we serve traffic? 
    Checks DB and Redis connectivity.
    """
    status = {
        "database": False,
        "redis": False
    }
    
    # 1. Check Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            status["database"] = True
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))

    # 2. Check Redis
    try:
        await redis_client.ping()
        status["redis"] = True
    except Exception as e:
        logger.error("health_check_redis_failed", error=str(e))

    # Decision Logic
    if all(status.values()):
        return {"status": "ready", "components": status}
    
    # Return 503 so K8s stops sending traffic
    response.status_code = 503
    return {"status": "unhealthy", "components": status}