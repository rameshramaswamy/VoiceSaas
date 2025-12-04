import structlog
from fastapi import WebSocket, WebSocketDisconnect
from app.pipeline.orchestrator import Orchestrator

logger = structlog.get_logger()

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Each call gets its own Orchestrator instance (State Machine)
    orchestrator = Orchestrator(websocket)
    
    try:
        logger.info("twilio_connected")
        
        # Start the pipeline
        await orchestrator.start()
        
        while True:
            # Receive raw messages from Twilio
            message = await websocket.receive_json()
            
            # Delegate to Orchestrator to decide what to do
            await orchestrator.handle_twilio_message(message)
            
    except WebSocketDisconnect:
        logger.info("twilio_disconnected")
        await orchestrator.cleanup()
    except Exception as e:
        logger.error("connection_error", error=str(e))
        await websocket.close()