import asyncio
import audioop

class JitterBuffer:
    def __init__(self, min_size=320):
        self.queue = asyncio.Queue()
        self.min_size = min_size
        self.buffer = b""

    async def put(self, chunk: bytes):
        await self.queue.put(chunk)

    async def get_stream(self):
        """Yields perfectly sized chunks for the provider"""
        while True:
            chunk = await self.queue.get()
            if chunk is None: break # EOF
            
            self.buffer += chunk
            
            # Emit in chunks of min_size (20ms at 8khz PCM16)
            while len(self.buffer) >= self.min_size:
                emit = self.buffer[:self.min_size]
                self.buffer = self.buffer[self.min_size:]
                yield emit