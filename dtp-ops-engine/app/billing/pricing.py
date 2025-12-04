class Pricing:
    # Costs in USD (or Credit Units)
    STT_PER_MIN = 0.01   # Deepgram
    TTS_PER_CHAR = 0.00003 # ElevenLabs
    LLM_IN_TOKEN = 0.00001 # GPT-3.5/4o-mini
    LLM_OUT_TOKEN = 0.00003
    PLATFORM_FEE_PER_CALL = 0.05