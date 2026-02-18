"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from pydantic import model_validator
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
    JWT_REFRESH_SECRET: str = "change-me-refresh"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption
    ENCRYPTION_KEY: str = "change-me"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Cookies
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True

    # App
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode='after')
    def _reject_insecure_defaults(self) -> "Settings":
        insecure = []
        if self.JWT_SECRET == "change-me":
            insecure.append("JWT_SECRET")
        if self.JWT_REFRESH_SECRET == "change-me-refresh":
            insecure.append("JWT_REFRESH_SECRET")
        if self.ENCRYPTION_KEY == "change-me":
            insecure.append("ENCRYPTION_KEY")
        if insecure:
            raise ValueError(
                f"Insecure default value(s) detected for: {', '.join(insecure)}. "
                "Please set secure secret(s) via environment variables or .env file."
            )
        return self


settings = Settings()
