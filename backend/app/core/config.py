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

    # Photo-assessment deployment configuration. Both paths must be supplied
    # by the deployment; there is deliberately no built-in taxonomy, crop list
    # or operating point.
    assessment_policy_path: str | None = None
    model_registry_path: str | None = None
    assessment_inference_timeout_s: float = 5.0
    assessment_inference_attempts: int = 2

    # Logging: one JSON event per line, no payloads and no PII.
    log_level: str = "INFO"

    # Interactive API docs are for dev/staging only; production may disable them.
    docs_enabled: bool = True

    # SQLAlchemy URL. The pilot runs PostgreSQL 16 + PostGIS; tests that do not
    # touch a database never open this connection.
    database_url: str = "postgresql+psycopg://ps03:ps03@localhost:5432/ps03"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
