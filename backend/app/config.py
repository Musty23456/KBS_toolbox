"""
Centralized application settings, loaded from environment variables / .env.

No secrets are hardcoded here — everything comes from the environment so the
same code works across local development, CI, and production.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

    APP_NAME: str = "KBS Toolbox API"
    APP_ENV: str = "development"

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    DATABASE_URL: str = "sqlite:///./kbs_toolbox.db"

    # ---------------------------------------------------------
    # JWT Authentication
    # ---------------------------------------------------------

    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---------------------------------------------------------
    # CORS
    # ---------------------------------------------------------

    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000"
    )

    # ---------------------------------------------------------
    # Rate Limiting
    # ---------------------------------------------------------

    RATE_LIMIT_PER_MINUTE: int = 60

    # ---------------------------------------------------------
    # Media
    # ---------------------------------------------------------

    MEDIA_ROOT: str = "./media"

    # ---------------------------------------------------------
    # Demo / Seed Data
    # ---------------------------------------------------------

    SEED_DEMO_DATA: bool = True

    DEMO_ADMIN_EMAIL: str = "admin@kbstoolbox.app"
    DEMO_ADMIN_PASSWORD: str = "ChangeMe123!"

    # ---------------------------------------------------------
    # Resend Email Configuration
    # ---------------------------------------------------------
    #
    # Password-reset emails are sent through the Resend HTTPS API.
    #
    # IMPORTANT:
    # Never put the real RESEND_API_KEY directly in this file.
    # Set it as an environment variable in Render.
    #

    RESEND_API_KEY: str = ""

    RESEND_FROM_EMAIL: str = ""

    # ---------------------------------------------------------
    # Web Application
    # ---------------------------------------------------------

    WEB_APP_URL: str = "http://localhost:5173"

    # ---------------------------------------------------------
    # Password Reset
    # ---------------------------------------------------------

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ---------------------------------------------------------
    # Helper Properties
    # ---------------------------------------------------------

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Convert the comma-separated CORS_ALLOWED_ORIGINS string
        into a clean list of origins.
        """

        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        """
        Return True when the application is running in production.
        """

        return self.APP_ENV.lower() == "production"


# -------------------------------------------------------------
# Cached Settings
# -------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    """
    Return the application settings.

    lru_cache ensures the Settings object is created only once
    during the application's lifetime.
    """

    return Settings()
