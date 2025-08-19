"""Application settings using Pydantic for environment variable validation."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    url: str = Field(
        default="sqlite+aiosqlite:///./rallycal.db",
        description="Database URL for SQLAlchemy",
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )
    pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    max_overflow: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Max overflow connections",
    )

    @validator("url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(
            (
                "sqlite+aiosqlite://",
                "postgresql+asyncpg://",
                "postgresql://",
                "sqlite:///",
            )
        ):
            msg = "Database URL must be SQLite or PostgreSQL"
            raise ValueError(msg)
        return v


class ServerSettings(BaseSettings):
    """Web server configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(
        default="0.0.0.0",
        description="Server host address",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
    )
    workers: int = Field(
        default=1,
        ge=1,
        le=32,
        description="Number of worker processes",
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development",
    )
    log_level: str = Field(
        default="info",
        description="Uvicorn log level",
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"critical", "error", "warning", "info", "debug", "trace"}
        if v.lower() not in valid_levels:
            msg = f"Log level must be one of: {valid_levels}"
            raise ValueError(msg)
        return v.lower()


class CalendarSettings(BaseSettings):
    """Calendar processing configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="CALENDAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    config_file: Path = Field(
        default=Path("config/calendars.yaml"),
        description="Path to calendar configuration file",
    )
    fetch_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout for calendar fetch requests in seconds",
    )
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed requests",
    )
    cache_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds",
    )
    max_events_per_calendar: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum events to process per calendar",
    )

    @validator("config_file")
    def validate_config_file(cls, v: Path) -> Path:
        """Validate configuration file path."""
        if v.suffix.lower() not in {".yaml", ".yml"}:
            msg = "Configuration file must be YAML format"
            raise ValueError(msg)
        return v


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        min_length=32,
        description="Secret key for signing tokens",
    )
    webhook_secret: str | None = Field(
        default=None,
        description="Secret for validating Git webhooks",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Rate limit requests per minute",
    )

    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            msg = "Secret key must be at least 32 characters"
            raise ValueError(msg)
        return v


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(
        default="RallyCal",
        description="Application name",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    environment: str = Field(
        default="development",
        description="Application environment",
    )

    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    calendar: CalendarSettings = Field(default_factory=CalendarSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_envs = {"development", "testing", "staging", "production"}
        if v.lower() not in valid_envs:
            msg = f"Environment must be one of: {valid_envs}"
            raise ValueError(msg)
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()
