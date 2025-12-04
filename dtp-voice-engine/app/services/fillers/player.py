import asyncio
import random
import os

class FillerPlayer:
    def __init__(self, websocket):
        self.ws = websocket
        self.stream_sid = None
        self.task = None
        self.active = False
        
        # Load filler audio (u-law format) into memory
        # In prod, load from disk or S3
        self.fillers = [
            # Dummy bytes representing 500ms of silence/breath/hmm
            # You must replace this with real `audioop.lin2ulaw` bytes
            b'\xff' * 1000 
        ]

    def set_stream_id(self, sid):
        self.stream_sid = sid

    def start_timer(self):
        """Starts a timer. If expired, play filler."""
        self.stop_timer() # Reset existing
        self.active = True
        self.task = asyncio.create_task(self._wait_and_play())

    def stop_timer(self):
        """Called when LLM starts streaming tokens (latency gap closed)."""
        self.active = False
        if self.task:
            self.task.cancel()
            self.task = None

    async def _wait_and_play(self):
        try:
            # Wait 800ms. If OpenAI responds faster, this cancels.
            await asyncio.sleep(0.8) 
            
            if self.active and self.stream_sid:
                # Play Filler
                import base64
                filler_chunk = random.choice(self.fillers)
                payload = base64.b64encode(filler_chunk).decode('utf-8')
                
                await self.ws.send_json({
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload}
                })
        except asyncio.CancelledError:
            pass