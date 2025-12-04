import asyncio
import base64
import structlog
from fastapi import WebSocket

from app.services.stt.deepgram import DeepgramSTT
from app.services.llm.openai_stream import OpenAIStream
from app.services.tts.elevenlabs import ElevenLabsTTS

logger = structlog.get_logger()

class Orchestrator:
    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.stream_sid = None
        
        # Instantiate the real services
        self.stt = DeepgramSTT()
        self.llm = OpenAIStream()
        self.tts = ElevenLabsTTS()
        
        self.is_speaking = False
        self.call_active = True
        self.current_tts_task = None

    async def start(self):
        """Connect to STT and start listening loop"""
        await self.stt.connect()
        asyncio.create_task(self.process_transcripts())

    async def handle_twilio_message(self, message: dict):
        event = message.get("event")
        
        if event == "start":
            self.stream_sid = message['start']['streamSid']
            logger.info("stream_started", sid=self.stream_sid)
            
        elif event == "media":
            payload = message['media']['payload']
            # Twilio sends base64 mulaw
            audio_chunk = base64.b64decode(payload)
            # Deepgram is configured to accept mulaw directly, no conversion needed on input!
            await self.stt.send_audio(audio_chunk)
            
        elif event == "stop":
            logger.info("stream_stopped")
            self.call_active = False

    async def process_transcripts(self):
        async for text in self.stt.get_transcript():
            if not text: continue
            
            logger.info("user_said", text=text)
            
            # 1. Interruption: If we are talking, STOP immediately.
            if self.is_speaking:
                await self.interrupt_call()
            
            # 2. Generate Response
            self.current_tts_task = asyncio.create_task(self.generate_response(text))

    async def generate_response(self, user_text: str):
        self.is_speaking = True
        try:
            # Get streams
            token_stream = self.llm.get_response_stream(
                prompt=user_text,
                system_prompt="You are a helpful AI assistant. Keep answers short and conversational."
            )
            audio_stream = self.tts.stream_audio(token_stream)
            
            async for audio_chunk in audio_stream:
                if not self.call_active: break
                
                # Check cancellation (Interruption)
                if asyncio.current_task().cancelled():
                    break

                # Send to Twilio
                payload = base64.b64encode(audio_chunk).decode('utf-8')
                media_message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload}
                }
                await self.ws.send_json(media_message)
        
        except asyncio.CancelledError:
            logger.info("tts_cancelled_by_interruption")
        except Exception as e:
            logger.error("generation_error", error=str(e))
        finally:
            self.is_speaking = False

    async def interrupt_call(self):
        """Handles Barge-In logic"""
        logger.info("interrupting_call")
        
        # 1. Cancel the Python task generating audio
        if self.current_tts_task:
            self.current_tts_task.cancel()
            
        # 2. Tell Twilio to clear its audio buffer
        clear_msg = {
            "event": "clear",
            "streamSid": self.stream_sid
        }
        await self.ws.send_json(clear_msg)

    async def cleanup(self):
        self.call_active = False