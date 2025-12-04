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

class ElevenLabsTTS(TTSService):
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.DEFAULT_VOICE_ID
        self.ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_turbo_v2"

    async def stream_audio(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Connects to ElevenLabs WebSocket, pushes text, receives audio.
        """
        async with websockets.connect(self.ws_url) as ws:
            # 1. Send Initial Config (PCM 8k is not supported natively by EL WS usually, 
            # they support mp3 or pcm_44100. We ask for pcm_44100 and downsample locally)
            await ws.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "xi_api_key": self.api_key,
                "authorization": self.api_key # Redundant but safe
            }))

            # 2. Create Tasks for Sending (Text) and Receiving (Audio)
            
            async def sender():
                """Reads from LLM stream and sends to ElevenLabs"""
                buffer = ""
                async for token in text_stream:
                    buffer += token
                    # Optimization: Send on space/punctuation to reduce latency
                    if " " in buffer or any(p in buffer for p in [".", ",", "!", "?"]):
                        await ws.send(json.dumps({"text": buffer, "try_trigger_generation": True}))
                        buffer = ""
                
                # Send remaining buffer
                if buffer:
                    await ws.send(json.dumps({"text": buffer}))
                
                # Send End of Stream
                await ws.send(json.dumps({"text": ""})) 

            async def receiver():
                """Reads audio from ElevenLabs and yields bytes"""
                while True:
                    try:
                        message = await ws.recv()
                        data = json.loads(message)
                        
                        if data.get("audio"):
                            # Base64 decode
                            audio_chunk = base64.b64decode(data["audio"])
                            
                            # ElevenLabs sends PCM 44.1kHz (usually). 
                            # We need to convert to 8kHz u-law for Twilio.
                            # Step A: Resample 44100 -> 8000
                            resampled = AudioUtils.resample_audio(audio_chunk, 44100, 8000)
                            
                            # Step B: Encode PCM -> Mulaw
                            mulaw_chunk = AudioUtils.pcm_to_mulaw(resampled)
                            
                            yield mulaw_chunk
                            
                        if data.get("isFinal"):
                            break
                    except websockets.exceptions.ConnectionClosed:
                        break

            # Run both concurrently
            send_task = asyncio.create_task(sender())
            
            # Yield audio as it arrives
            async for chunk in receiver():
                yield chunk
            
            await send_task # Ensure sender finishes