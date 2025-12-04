from fastapi import FastAPI
from app.core.cache import redis_client
from app.db.session import engine
import structlog

logger = structlog.get_logger()

def register_lifecycle_events(app: FastAPI):
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("app_startup", message="Initializing connections...")
        # (Optional) Pre-warm cache or load secrets here
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("app_shutdown", message="Closing connections...")
        
        # 1. Close Redis
        await redis_client.close()
        
        # 2. Close DB Engine
        await engine.dispose()
        
        logger.info("app_shutdown_complete", message="Cleanup done.")