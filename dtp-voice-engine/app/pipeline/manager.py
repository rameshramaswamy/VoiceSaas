import asyncio
import base64
import structlog
from typing import Optional, Set

from fastapi import WebSocket

# Services
from app.services.stt.deepgram import DeepgramSTT
from app.services.llm.openai_stream import OpenAIStream
from app.services.tts.elevenlabs_robust import ElevenLabsRobust
from app.services.vad.local import LocalVAD
from app.services.fillers.player import FillerPlayer
from app.services.tts.cache import AudioCache

# Utilities
from app.utils.audio import AudioUtils
from app.utils.text_processing import TextStreamer
from app.pipeline.context import ContextManager
from app.events.producer import EventProducer
# Observability
from app.core.telemetry import LatencyTracker, CALL_COUNTER, ERROR_COUNTER

logger = structlog.get_logger()

class CallManager:
    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.stream_sid: str = "unknown"
        self.tracker: Optional[LatencyTracker] = None
        
        # --- Architecture Components ---
        self.stt = DeepgramSTT()
        self.llm = OpenAIStream()
        self.tts = ElevenLabsRobust()
        self.vad = LocalVAD(threshold=0.5)
        self.filler_player = FillerPlayer(websocket)
        self.context = ContextManager(
            system_prompt="You are a helpful, professional AI assistant for DTP Enterprise. Keep responses concise and natural."
        )
        self.text_streamer = TextStreamer()
        
        # --- State Management ---
        self.is_speaking = False
        self.call_active = True
        
        # Track background tasks to prevent Garbage Collection (Asyncio "Fire and Forget" issue)
        self.active_tasks: Set[asyncio.Task] = set()
        self.current_generation_task: Optional[asyncio.Task] = None
        self.producer = EventProducer(redis_url=settings.REDIS_URL)
        self.usage_metrics = {
            "duration": 0, 
            "prompt_tokens": 0, 
            "completion_tokens": 0, 
            "tts_chars": 0
        }

    async def start(self):
        """
        Initializes the pipeline. Connects to vendors and starts listening loops.
        """
        try:
            CALL_COUNTER.inc()
            
            # 1. Parallel Connection to Vendors (Reduce Cold Start)
            await asyncio.gather(
                self.stt.connect(),
                self.tts.connect()
            )
            
            # 2. Start STT Processing Loop
            task = asyncio.create_task(self.process_transcripts())
            self._track_task(task)
            
            logger.info("pipeline_started")
            
        except Exception as e:
            logger.error("pipeline_start_failed", error=str(e))
            await self.ws.close()

    async def handle_twilio_message(self, message: dict):
        """
        Main Event Dispatcher for Twilio WebSocket Messages.
        """
        event = message.get("event")
        
        if event == "start":
            self.stream_sid = message['start']['streamSid']
            self.tracker = LatencyTracker(self.stream_sid)
            self.filler_player.set_stream_id(self.stream_sid)
            logger.info("stream_started", sid=self.stream_sid)
            
        elif event == "media":
            await self._handle_media(message)
            
        elif event == "stop":
            logger.info("stream_stopped", sid=self.stream_sid)
            self.call_active = False
            
        elif event == "mark":
            # Can be used to track when audio actually finished playing on user device
            pass

    async def _handle_media(self, message: dict):
        """
        Processes raw audio: VAD Check -> STT Push
        """
        try:
            payload = message['media']['payload']
            chunk = base64.b64decode(payload)
            
            # 1. VAD Check (Barge-In)
            # Twilio sends mulaw. Convert to PCM for VAD analysis.
            pcm_chunk = AudioUtils.mulaw_to_pcm(chunk)
            
            if self.is_speaking and self.vad.is_speech(pcm_chunk):
                logger.info("vad_barge_in_triggered", sid=self.stream_sid)
                await self.interrupt_call()
            
            # 2. Push to STT
            # Deepgram is configured to accept mulaw directly
            await self.stt.send_audio(chunk)
            
        except Exception as e:
            logger.error("media_processing_error", error=str(e))

    async def process_transcripts(self):
        """
        Consumes text from STT and triggers response generation.
        """
        try:
            async for text in self.stt.get_transcript():
                if not text or not text.strip(): 
                    continue
                
                logger.info("user_transcript", text=text, sid=self.stream_sid)
                
                # If we were speaking, stop immediately (Double safety with VAD)
                if self.is_speaking:
                    await self.interrupt_call()
                
                # Start Metrics
                if self.tracker: self.tracker.start_turn()
                
                # Cancel any previous generation that might be lingering
                if self.current_generation_task and not self.current_generation_task.done():
                    self.current_generation_task.cancel()
                
                # Start Generation
                self.current_generation_task = asyncio.create_task(self.generate_response(text))
                self._track_task(self.current_generation_task)
                
        except asyncio.CancelledError:
            logger.info("transcript_loop_cancelled")
        except Exception as e:
            logger.error("stt_loop_failed", error=str(e))
            ERROR_COUNTER.labels(type="stt_loop").inc()

    async def generate_response(self, user_text: str):
        """
        The Core Logic: Context -> Cache -> Fillers -> LLM -> TTS
        """
        self.is_speaking = True
        
        # 1. Update Context
        self.context.add_user_message(user_text)
        
        # 2. Start Latency Masking (Filler Audio)
        self.filler_player.start_timer()
        
        try:
            # 3. Check Audio Cache (0ms Latency for "Hello", "Bye", etc.)
            # Need a voice_id context, using default for now
            cached_audio = await AudioCache.get(user_text, self.tts.voice_id)
            if cached_audio:
                logger.info("cache_hit", text=user_text[:20])
                self.filler_player.stop_timer()
                if self.tracker: self.tracker.mark("cache_hit")
                
                await self._send_audio(cached_audio)
                self.context.add_assistant_message(user_text) # Assumes cache key is roughly the text
                return

            # 4. Stream LLM
            messages = self.context.get_messages_for_llm()
            if self.tracker: self.tracker.mark("llm_req_start")
            self.usage_metrics["completion_tokens"] += 1
            token_stream = self.llm.get_response_stream(user_text, system_prompt=self.context.system_prompt["content"])
            
            full_response_buffer = ""
            
            async for token in token_stream:
                if not self.call_active: break
                
                # Stop Filler as soon as intelligence arrives
                self.filler_player.stop_timer()
                if self.tracker and not full_response_buffer: 
                    self.tracker.mark("llm_first_token")
                
                full_response_buffer += token
                
                # 5. Smart Buffering (Send phrases, not just sentences)
                chunk_text = self.text_streamer.consume(token)
                self.usage_metrics["tts_chars"] += len(chunk_text)
                if chunk_text:
                    await self._stream_tts_chunk(chunk_text)
            
            # Flush remaining text in buffer
            last_chunk = self.text_streamer.flush()
            if last_chunk:
                await self._stream_tts_chunk(last_chunk)
                
            # Update Context with full AI response
            self.context.add_assistant_message(full_response_buffer)

        except asyncio.CancelledError:
            logger.info("generation_cancelled_interruption", sid=self.stream_sid)
        except Exception as e:
            logger.error("generation_error", error=str(e), sid=self.stream_sid)
            ERROR_COUNTER.labels(type="generation").inc()
        finally:
            self.filler_player.stop_timer()
            self.is_speaking = False

    async def _stream_tts_chunk(self, text: str):
        """
        Helper: Sends text to TTS and streams resulting audio to Twilio.
        """
        if self.tracker: self.tracker.mark("tts_req_start")
        
        # Assuming stream_audio returns a generator of bytes (mulaw)
        # Note: ElevenLabsRobust.stream_audio takes a generator, 
        # so we wrap this single chunk in a simple async generator
        async def single_chunk_gen():
            yield text
            
        audio_stream = self.tts.stream_audio(single_chunk_gen())
        
        first_byte_sent = False
        
        async for audio_chunk in audio_stream:
            if not self.call_active: break
            
            if asyncio.current_task().cancelled():
                break

            await self._send_audio(audio_chunk)
            
            if not first_byte_sent:
                if self.tracker: self.tracker.end_turn() # Metric: Time to First Audio
                first_byte_sent = True

    async def _send_audio(self, chunk: bytes):
        """
        Encodes and sends audio frame to Twilio.
        """
        payload = base64.b64encode(chunk).decode('utf-8')
        try:
            await self.ws.send_json({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": payload}
            })
        except Exception:
            # WebSocket might be closed
            self.call_active = False

    async def interrupt_call(self):
        """
        Hard Stop: Cancels generation and clears Twilio's audio buffer.
        """
        logger.info("interrupting_call", sid=self.stream_sid)
        
        # 1. Stop Filler
        self.filler_player.stop_timer()
        
        # 2. Cancel current generation task
        if self.current_generation_task and not self.current_generation_task.done():
            self.current_generation_task.cancel()
            
        # 3. Tell Twilio to clear buffer (Silence immediately)
        if self.stream_sid:
            try:
                await self.ws.send_json({
                    "event": "clear",
                    "streamSid": self.stream_sid
                })
            except Exception:
                pass
        
        self.is_speaking = False

    def _track_task(self, task: asyncio.Task):
        """
        Adds task to strong reference set to prevent GC execution failure.
        """
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)

    async def cleanup(self):
        """
        Graceful shutdown of resources.
        """
        self.call_active = False
        self.filler_player.stop_timer()
        
        # Cancel all background tasks
        for task in self.active_tasks:
            task.cancel()
            
        # Close vendor connections
        await self.tts.close()
        
        logger.info("pipeline_cleanup_complete", sid=self.stream_sid)

       # Publish Billing Event
        duration = time.time() - self.start_time
        event_payload = {
            "tenant_id": self.tenant_id, # Passed from connection params
            "call_id": self.stream_sid,
            "duration_sec": duration,
            "prompt_tokens": self.usage_metrics["prompt_tokens"],
            "completion_tokens": self.usage_metrics["completion_tokens"],
            "tts_chars": self.usage_metrics["tts_chars"]
        }
        
        await self.producer.publish("call.ended", event_payload)