"""Application settings.

Values come from environment variables prefixed with ``APP_`` or from a local
``.env`` file. No secrets belong in source control.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "PS-03 API"
    environment: str = "dev"
    version: str = "0.1.0"
    api_v1_prefix: str = "/v1"
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
