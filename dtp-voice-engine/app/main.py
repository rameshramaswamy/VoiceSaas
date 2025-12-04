import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from prometheus_client import make_asgi_app

from app.pipeline.manager import CallManager
from app.core.logging import configure_logging

# 1. Setup Logging
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title="DTP Enterprise Voice Engine")

# 2. Prometheus Metrics Endpoint (/metrics)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.websocket("/streams/twilio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager = CallManager(websocket)
    
    try:
        await manager.start()
        while True:
            data = await websocket.receive_json()
            await manager.handle_twilio_message(data)
    except WebSocketDisconnect:
        logger.info("client_disconnected")
    except Exception as e:
        logger.error("fatal_error", error=str(e))
    finally:
        await manager.cleanup()

@app.get("/health")
def health():
    return {"status": "ok"}