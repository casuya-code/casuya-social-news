"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is the parent of the server-python directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED_SCHEMAS_DIR = PROJECT_ROOT / "shared" / "schemas"


class Settings(BaseSettings):
    """Central configuration. Values come from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "server-python" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_debug: bool = True

    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://casuya_user:password@localhost:5432/casuya_db"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis (optional)
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    jwt_refresh_token_expire_days: int = 30
    api_key: str = "dev-api-key"
    # Operator credentials used as fallback when the DB is offline.
    admin_username: str = "admin"
    admin_password: str = "admin"

    # TTS
    tts_provider: str = "mock"  # mock | google_cloud | elevenlabs
    google_cloud_project: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_monthly_budget_usd: float = 50.0

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # NLP
    script_generation_timeout_seconds: float = 30.0

    # External news / weather
    news_api_key: str = ""
    openweather_api_key: str = ""
    # Rotate mock-feed URLs each round so the endless loop / tests always get
    # fresh stories (off by default: stable dev dedupe behaviour).
    mock_feed_rotate: bool = False

    # Storage
    storage_backend: str = "local"  # local | s3
    storage_local_path: str = str(PROJECT_ROOT / "server-python" / "storage")
    cdn_base_url: str = "http://localhost:8000/storage"
    aws_s3_bucket: str = Field("", validation_alias="STORAGE_S3_BUCKET")
    aws_s3_region: str = Field("us-east-1", validation_alias="STORAGE_S3_REGION")
    aws_access_key_id: str = Field("", validation_alias="STORAGE_S3_ACCESS_KEY")
    aws_secret_access_key: str = Field("", validation_alias="STORAGE_S3_SECRET_KEY")

    # Rate limiting
    rate_limit_api: str = "60/minute"
    rate_limit_voice: str = "5/minute"
    trusted_proxies: str = ""  # comma-separated proxy IPs to trust for X-Forwarded-For

    # Background scheduler (endless-stories loop)
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 300
    # scheduler_backend: "inprocess" runs the asyncio loop inside the server;
    # "celery" defers ingestion to a Celery worker + beat (Redis broker).
    scheduler_backend: str = "inprocess"
    # Run the retention sweep every N ingest cycles (audio purge + DB cleanup).
    retention_enabled: bool = True
    retention_cycle_frequency: int = 12  # ~1h at the default 300s interval

    # CORS (comma-separated origins, empty = no browser access)
    allowed_origins: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def storage_dir(self) -> Path:
        """Return the local storage directory, creating it if needed."""
        path = Path(self.storage_local_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_production_secrets(self) -> None:
        """Raise if sensitive defaults are unchanged in production."""
        if self.app_env != "production":
            return
        _insecure = {
            "jwt_secret_key": self.jwt_secret_key,
            "api_key": self.api_key,
            "admin_password": self.admin_password,
        }
        defaults = {
            "jwt_secret_key": "change-me",
            "api_key": "dev-api-key",
            "admin_password": "admin",
        }
        insecure = [k for k, v in _insecure.items() if v == defaults.get(k)]
        if insecure:
            raise ValueError(
                f"Insecure defaults in production: {', '.join(insecure)}. "
                "Set these in .env before deploying."
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-reading .env)."""
    return Settings()
