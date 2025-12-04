from fastapi import HTTPException, Request, Depends
from app.core.cache import redis_client
import time

class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests # Max requests
        self.window = window     # Per window (seconds)

    async def __call__(self, request: Request):
        # 1. Identify User/Tenant
        # In a real scenario, extract tenant_id from JWT in headers
        # For now, fallback to IP if auth not present
        identifier = request.headers.get("X-Tenant-ID", request.client.host)
        
        key = f"rate_limit:{identifier}:{int(time.time() // self.window)}"
        
        # 2. Increment Counter
        current_count = await redis_client.incr(key)
        
        # 3. Set Expiry on first request
        if current_count == 1:
            await redis_client.expire(key, self.window)
            
        # 4. Check Limit
        if current_count > self.requests:
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests. Please slow down."
            )