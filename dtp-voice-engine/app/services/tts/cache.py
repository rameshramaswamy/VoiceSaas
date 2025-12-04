import hashlib
from typing import Optional
from app.core.cache import redis_client # Reusing from Control Plane or new instance

class AudioCache:
    """
    Caches TTS audio bytes for common phrases.
    Key: Hash(Text + VoiceID) -> Value: Bytes (ulaw)
    """
    @staticmethod
    def _hash_key(text: str, voice_id: str) -> str:
        raw = f"{text.strip().lower()}:{voice_id}"
        return hashlib.md5(raw.encode()).hexdigest()

    @staticmethod
    async def get(text: str, voice_id: str) -> Optional[bytes]:
        # Only cache short phrases
        if len(text) > 50: return None
        
        key = AudioCache._hash_key(text, voice_id)
        # Assuming redis_client handles bytes
        # In prod, you might need base64 decoding here depending on redis lib config
        return await redis_client.get(key)

    @staticmethod
    async def set(text: str, voice_id: str, audio: bytes):
        if len(text) > 50: return
        key = AudioCache._hash_key(text, voice_id)
        # Cache for 24 hours
        await redis_client.set(key, audio, ex=86400)