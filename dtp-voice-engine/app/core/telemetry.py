import time
import structlog
from contextlib import contextmanager
from prometheus_client import Histogram, Counter

# Prometheus Metrics
LATENCY_HISTOGRAM = Histogram(
    'voice_latency_seconds', 
    'Time from User Stop Speaking to AI Audio Start',
    buckets=[0.5, 0.8, 1.0, 1.5, 2.0]
)
CALL_COUNTER = Counter('total_calls', 'Total number of voice calls')
ERROR_COUNTER = Counter('call_errors', 'Total errors', ['type'])

logger = structlog.get_logger()

class LatencyTracker:
    def __init__(self, stream_sid: str):
        self.stream_sid = stream_sid
        self.start_time = 0
        self.checkpoints = {}

    def start_turn(self):
        """Called when user stops speaking (STT Final)"""
        self.start_time = time.perf_counter()
        self.checkpoints = {"start": self.start_time}
        logger.info("turn_started", stream_sid=self.stream_sid)

    def mark(self, event: str):
        """Mark LLM_start, TTS_start, etc."""
        now = time.perf_counter()
        self.checkpoints[event] = now
        duration = (now - self.start_time) * 1000 # ms
        logger.debug(f"latency_checkpoint_{event}", stream_sid=self.stream_sid, ms=int(duration))

    def end_turn(self):
        """Called when first byte of audio is sent to Twilio"""
        if self.start_time == 0: return
        
        duration = time.perf_counter() - self.start_time
        LATENCY_HISTOGRAM.observe(duration)
        
        logger.info(
            "turn_complete_v2v", 
            stream_sid=self.stream_sid, 
            latency_ms=int(duration * 1000),
            breakdown={k: int((v - self.start_time)*1000) for k,v in self.checkpoints.items()}
        )
        self.start_time = 0 # Reset