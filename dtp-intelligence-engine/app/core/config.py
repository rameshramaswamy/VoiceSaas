from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    PORT: int = 8090
    ENV: str = "development"
    
    # AI Keys
    OPENAI_API_KEY: str
    
    # Vector DB
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "dtp-knowledge-base"
    PINECONE_ENV: str = "us-east-1" # or serverless region
    # Google Calendar Integration
    GOOGLE_SERVICE_ACCOUNT_JSON: str = "" # Base64 encoded JSON or path
    
    # Localization
    DEFAULT_FALLBACK_LANGUAGE: str = "en-US"
    class Config:
        env_file = ".env"

settings = Settings()