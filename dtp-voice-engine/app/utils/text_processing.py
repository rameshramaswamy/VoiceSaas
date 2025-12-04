import re

class TextStreamer:
    """
    Splits a stream of tokens into sendable chunks for TTS.
    Optimized for low latency by splitting on commas/conjunctions.
    """
    def __init__(self):
        self.buffer = ""
        # Split on punctuation (. ? !) OR commas/semicolons (, ;)
        # Also could split on " and ", " but " etc.
        self.split_pattern = re.compile(r'([.,;?!])')

    def consume(self, token: str):
        self.buffer += token
        
        # Check if we have a sendable chunk
        match = self.split_pattern.search(self.buffer)
        if match:
            # Find the split point
            split_idx = match.end()
            chunk = self.buffer[:split_idx]
            self.buffer = self.buffer[split_idx:]
            
            # Heuristic: Don't send tiny chunks like "No," (wait for more context)
            if len(chunk.strip()) < 3 and "," in chunk:
                 # Put it back, wait for more
                 self.buffer = chunk + self.buffer
                 return None
                 
            return chunk.strip()
        
        return None

    def flush(self):
        ret = self.buffer
        self.buffer = ""
        return ret.strip()