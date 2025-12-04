import audioop

class AudioUtils:
    @staticmethod
    def mulaw_to_pcm(mulaw_chunk: bytes) -> bytes:
        # Use simple audioop, it's C-optimized and fast enough
        return audioop.ulaw2lin(mulaw_chunk, 2)

    @staticmethod
    def pcm_to_mulaw(pcm_chunk: bytes) -> bytes:
        return audioop.lin2ulaw(pcm_chunk, 2)

    @staticmethod
    def create_vad_chunk(buffer: bytearray) -> bytes:
        """Returns a view of the buffer for VAD processing"""
        # VAD typically needs ~30ms-50ms windows
        return bytes(buffer)