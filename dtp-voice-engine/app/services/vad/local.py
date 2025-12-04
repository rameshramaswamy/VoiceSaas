import onnxruntime
import numpy as np
import structlog
import os

logger = structlog.get_logger()

class LocalVAD:
    def __init__(self, threshold=0.5):
        self.session = None
        self.threshold = threshold
        self.h = np.zeros((2, 1, 64), dtype=np.float32)
        self.c = np.zeros((2, 1, 64), dtype=np.float32)
        self.sr = 8000
        
        # Load Model (Ensure silero_vad.onnx is downloaded in Docker build)
        model_path = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")
        if not os.path.exists(model_path):
            # Fallback or error - for now we assume it exists
            # In production, download this during Docker build
            pass
            
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1 
        opts.intra_op_num_threads = 1 # Optimize for single core per call
        
        try:
            self.session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'], sess_options=opts)
        except Exception:
            logger.warning("vad_model_missing", msg="Running without local VAD")

    def is_speech(self, audio_chunk: bytes) -> bool:
        """
        Input: 8khz PCM bytes
        Output: True if speech detected
        """
        if not self.session: return False
        
        # Convert bytes to float32 array
        audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        # Add batch dimension
        input_tensor = audio_float32[np.newaxis, :]
        
        ort_inputs = {
            'input': input_tensor,
            'sr': np.array([self.sr], dtype=np.int64),
            'h': self.h,
            'c': self.c
        }
        
        # Run Inference (< 1ms usually)
        out, self.h, self.c = self.session.run(None, ort_inputs)
        
        probability = out[0][0]
        return probability > self.threshold