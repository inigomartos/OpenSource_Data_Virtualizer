"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://datamind:yourpassword@localhost:5432/datamind_app"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI
    ANTHROPIC_API_KEY: str = ""

    # Auth
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption
    ENCRYPTION_KEY: str = "change-me"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # App
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
