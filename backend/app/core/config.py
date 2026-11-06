"""Application settings.

Values come from environment variables prefixed with ``APP_`` or from a local
``.env`` file. No secrets belong in source control.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "PS-03 API"
    environment: str = "dev"
    version: str = "0.2.0"
    api_v1_prefix: str = "/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Photo-assessment deployment configuration.
    assessment_policy_path: str | None = None
    model_registry_path: str | None = None
    assessment_inference_timeout_s: float = 5.0
    assessment_inference_attempts: int = 2

    # Logging: one JSON event per line, no payloads and no PII.
    log_level: str = "INFO"

    # Interactive API docs are for dev/staging only; production may disable them.
    docs_enabled: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    # Persistence. PostgreSQL 16 + PostGIS is the production target; SQLite
    # keeps local development and the test suite runnable without services.
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'var' / 'ps03.db').as_posix()}"
    seed_reference_data: bool = True
    seed_demo_users: bool = False

    # Bootstrap admin (development only; must be supplied through the
    # environment in any deployed setting).
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_mfa_secret: str | None = None

    # Tokens and sessions.
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    mfa_challenge_minutes: int = 5

    # OTP and authentication throttling.
    otp_ttl_minutes: int = 5
    otp_max_attempts: int = 5
    expose_otp_in_dev: bool = True
    auth_rate_limit_per_minute: int = 30

    # Media storage.
    storage_backend: str = "local"
    storage_root: Path = BACKEND_ROOT / "var" / "storage"
    upload_url_ttl_seconds: int = 900
    signed_url_ttl_seconds: int = 300
    max_upload_bytes: int = 12 * 1024 * 1024
    min_image_dimension: int = 480
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Versioned model inputs. Every prediction carries the version string it
    # was produced with; nothing here represents a trained production model.
    quality_gate_version: str = "demo-quality-gate-0.1"
    image_model_version: str = "demo-image-classifier-0.1"
    forecast_model_version: str = "demo-rules-forecast-0.1"

    # Forecast and coverage thresholds (demo configuration pending sign-off).
    forecast_horizon_days: int = 10
    weather_stale_hours: int = 24
    min_active_reporters: int = 3
    small_count_threshold: int = 5


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
