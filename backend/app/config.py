"""
Centralized application settings, loaded from environment variables / .env.
No secrets are hardcoded here — everything comes from the environment so the
same code works across local dev, CI, and production without modification.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "KBS Toolbox API"
    APP_ENV: str = "development"

    DATABASE_URL: str = "sqlite:///./kbs_toolbox.db"

    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    RATE_LIMIT_PER_MINUTE: int = 60
    MEDIA_ROOT: str = "./media"

    SEED_DEMO_DATA: bool = True
    DEMO_ADMIN_EMAIL: str = "admin@kbstoolbox.app"
    DEMO_ADMIN_PASSWORD: str = "ChangeMe123!"
    
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    SMTP_USE_TLS: bool = True

    WEB_APP_URL: str = "http://localhost:5173"

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
