import json
import asyncio
import structlog
from typing import AsyncGenerator
from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents

from app.core.config import settings
from app.services.base import STTService
from app.utils.audio import AudioUtils

logger = structlog.get_logger()

class DeepgramSTT(STTService):
    def __init__(self):
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.dg_connection = None
        self.transcript_queue = asyncio.Queue()
        self.is_connected = False

    async def connect(self):
        """Initializes the Deepgram WebSocket connection."""
        config = DeepgramClientOptions(options={"keepalive": "true"})
        self.dg_connection = self.client.listen.live.v("1")

        # Define Event Handlers
        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0 and result.is_final:
                # We only push "Final" transcripts to the LLM to avoid jitter
                self.transcript_queue.put_nowait(sentence)

        def on_error(self, error, **kwargs):
            logger.error("deepgram_error", error=error)

        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        # Start Connection with optimized settings for phone calls
        options = LiveOptions(
            model="nova-2-phone", # Optimized for Telephony
            language="en-US",
            smart_format=True,
            encoding="mulaw",     # Deepgram accepts mulaw directly!
            sample_rate=8000,
            interim_results=True, # We need these for VAD (future), but LLM uses final
            vad_events=True,
            endpointing=300       # 300ms silence = end of utterance
        )

        if self.dg_connection.start(options) is False:
            raise Exception("Failed to connect to Deepgram")
        
        self.is_connected = True
        logger.info("deepgram_connected")

    async def send_audio(self, audio_chunk: bytes):
        """Sends raw audio bytes to Deepgram."""
        if self.is_connected:
            # Send raw mulaw bytes directly since we configured encoding="mulaw"
            self.dg_connection.send(audio_chunk)

    async def get_transcript(self) -> AsyncGenerator[str, None]:
        """Yields transcripts from the queue as they arrive."""
        while True:
            transcript = await self.transcript_queue.get()
            yield transcript