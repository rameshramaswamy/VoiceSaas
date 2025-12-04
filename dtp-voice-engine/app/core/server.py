import uvicorn
import uvloop
import asyncio
from app.core.config import settings

def run_server():
    """
    Entry point that configures the high-performance event loop.
    """
    # 1. Install uvloop policy
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # 2. Run Uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level="info",
        loop="uvloop",      # Explicitly use uvloop
        http="httptools",   # Faster HTTP parsing
        ws="websockets",    # Optimized WS implementation
        workers=1           # For async voice, 1 process per core is standard
    )

if __name__ == "__main__":
    run_server()