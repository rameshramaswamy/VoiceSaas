from abc import ABC, abstractmethod
from typing import AsyncGenerator

class STTService(ABC):
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def send_audio(self, audio_chunk: bytes):
        pass
    
    @abstractmethod
    async def get_transcript(self) -> AsyncGenerator[str, None]:
        pass

class LLMService(ABC):
    @abstractmethod
    async def get_response_stream(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        pass

class TTSService(ABC):
    @abstractmethod
    async def stream_audio(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        pass