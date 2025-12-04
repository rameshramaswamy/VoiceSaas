from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DTP Voice Platform"
    DATABASE_URL: str = "postgresql+asyncpg://dtp_admin:change_me@localhost:5432/dtp_core"
    SECRET_KEY: str = "SUPER_SECRET_KEY_FOR_JWT"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()