import asyncio
import websockets
import json
import base64
import structlog
from typing import AsyncGenerator
from app.core.config import settings
from app.services.base import TTSService
from app.utils.audio import AudioUtils

logger = structlog.get_logger()

class ElevenLabsRobust(TTSService):
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.DEFAULT_VOICE_ID
        self.ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_turbo_v2"
        self.ws = None

    async def connect(self):
        """Pre-connect to save time"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            # Send initial BOS (Beginning of Stream)
            await self.ws.send(json.dumps({
                "text": " ",
                "xi_api_key": self.api_key,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
            }))
            logger.info("elevenlabs_connected")
        except Exception as e:
            logger.error("elevenlabs_connection_failed", error=str(e))

    async def stream_audio(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        if not self.ws or self.ws.closed:
            await self.connect()

        async def sender():
            try:
                buffer = ""
                async for token in text_stream:
                    buffer += token
                    if " " in buffer or any(p in buffer for p in [".", "?", "!"]):
                        await self.ws.send(json.dumps({"text": buffer, "try_trigger_generation": True}))
                        buffer = ""
                if buffer:
                    await self.ws.send(json.dumps({"text": buffer}))
                await self.ws.send(json.dumps({"text": ""})) # EOS for this turn
            except Exception as e:
                logger.error("tts_send_error", error=str(e))

        async def receiver():
            try:
                while True:
                    msg = await self.ws.recv()
                    data = json.loads(msg)
                    if data.get("audio"):
                        chunk = base64.b64decode(data["audio"])
                        # Resample 44.1k -> 8k
                        resampled = AudioUtils.resample_audio(chunk, 44100, 8000)
                        yield AudioUtils.pcm_to_mulaw(resampled)
                    
                    if data.get("isFinal"):
                        break
            except Exception as e:
                logger.error("tts_receive_error", error=str(e))

        # Run concurrent
        asyncio.create_task(sender())
        async for chunk in receiver():
            yield chunk
            
    async def close(self):
        if self.ws:
            await self.ws.close()