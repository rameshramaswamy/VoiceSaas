from pydantic import BaseSettings

class Settings(BaseSettings):
    # App
    PORT: int = 8080
    ENV: str = "development"
    
    # Provider Keys
    DEEPGRAM_API_KEY: str
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    
    # Default Voice Settings
    DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" # Rachel
    
    class Config:
        env_file = ".env"

settings = Settings()