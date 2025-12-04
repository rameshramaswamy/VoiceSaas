import re
import structlog

logger = structlog.get_logger()

class PIIScrubber:
    """
    Sanitizes text to remove Emails, Phone Numbers, and Credit Cards 
    before ingestion.
    """
    
    # Pre-compiled Regex Patterns for Performance
    PATTERNS = {
        "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "PHONE": r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b(?:\d{4}[- ]?){3}\d{4}\b'
    }

    @staticmethod
    def scrub(text: str) -> str:
        scrubbed_text = text
        redacted_counts = {}

        for pii_type, pattern in PIIScrubber.PATTERNS.items():
            # Find all matches
            matches = re.findall(pattern, scrubbed_text)
            if matches:
                redacted_counts[pii_type] = len(matches)
                # Replace with placeholder <EMAIL_REDACTED>
                scrubbed_text = re.sub(pattern, f"<{pii_type}_REDACTED>", scrubbed_text)
        
        if redacted_counts:
            logger.warning("pii_detected_and_redacted", counts=redacted_counts)
            
        return scrubbed_text