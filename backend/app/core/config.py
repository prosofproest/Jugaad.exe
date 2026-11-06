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

    # Chat assessment engine. ``demo`` serves a deterministic, visibly labelled
    # synthetic result so the end-to-end path works without an external model.
    # Any other value fails closed with ``model_not_configured``; a real
    # provider is added behind the same seam once its key and governance
    # decision exist.
    chat_engine: str = "demo"

    # Chat image uploads. Local development storage only; a deployment replaces
    # this with object storage. No file is ever served without an owner check.
    media_root: str = "var/media"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_dimension: int = 8000

    # Logging: one JSON event per line, no payloads and no PII.
    log_level: str = "INFO"

    # Interactive API docs are for dev/staging only; production may disable them.
    docs_enabled: bool = True

    # SQLAlchemy URL. The pilot runs PostgreSQL 16 + PostGIS; tests that do not
    # touch a database never open this connection.
    database_url: str = "postgresql+psycopg://ps03:ps03@localhost:5432/ps03"

    # Identity (spec 03). The default secret is for local development only;
    # production startup refuses it. Tokens, OTPs and lockout limits are kept
    # here so a deployment can tune them without a code change.
    auth_secret: str = "dev-only-insecure-secret-change-me"
    auth_access_ttl_minutes: int = 15
    auth_refresh_ttl_days: int = 30
    auth_mfa_challenge_ttl_minutes: int = 5
    auth_otp_ttl_minutes: int = 5
    auth_otp_max_attempts: int = 5
    auth_otp_phone_limit: int = 5
    auth_otp_ip_limit: int = 20
    auth_otp_rate_window_minutes: int = 15
    auth_staff_failure_limit: int = 10
    auth_staff_lockout_minutes: int = 15

    # Decision D10 is open. ``None`` means a deleted account is soft-deleted
    # with no hard-delete date; do not invent a retention period here.
    auth_deletion_retention_days: int | None = None

    # First-admin bootstrap. Never a public endpoint and never logged. All
    # three values must be supplied together; the TOTP secret is the base32
    # seed the admin enrols in their authenticator.
    auth_bootstrap_admin_email: str | None = None
    auth_bootstrap_admin_password: str | None = None
    auth_bootstrap_admin_totp_secret: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
