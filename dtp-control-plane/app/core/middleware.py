import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class EnterpriseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Correlation ID (Trace ID)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 2. Contextualize Logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host
        )

        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            # 3. Log Performance
            process_time = time.perf_counter() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            if response.status_code >= 400:
                logger.error("request_failed", status_code=response.status_code, duration=process_time)
            else:
                logger.info("request_completed", status_code=response.status_code, duration=process_time)
                
            return response
            
        except Exception as e:
            # Catch unhandled exceptions to ensure logging happens
            process_time = time.perf_counter() - start_time
            logger.error("request_crashed", error=str(e), duration=process_time)
            raise e