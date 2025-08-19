"""Unit tests for Pydantic models with edge cases and validation scenarios."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from src.rallycal.config.models import (
    AuthConfig,
    AuthType,
    CalendarSource,
    ManualEvent,
)
from src.rallycal.core.settings import (
    CalendarSettings,
    DatabaseSettings,
    SecuritySettings,
    ServerSettings,
    Settings,
)
from src.rallycal.models.event import EventModel, EventStatus, EventType


class TestAuthConfig:
    """Test AuthConfig model validation."""

    @pytest.mark.unit
    def test_auth_config_none_type(self):
        """Test auth config with no authentication."""
        auth = AuthConfig(type=AuthType.NONE)
        assert auth.type == AuthType.NONE
        assert auth.token is None
        assert auth.username is None
        assert auth.password is None

    @pytest.mark.unit
    def test_auth_config_bearer_token(self):
        """Test auth config with bearer token."""
        auth = AuthConfig(type=AuthType.BEARER, token="test-token")
        assert auth.type == AuthType.BEARER
        assert auth.token == "test-token"

    @pytest.mark.unit
    def test_auth_config_bearer_missing_token(self):
        """Test auth config bearer type requires token."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(type=AuthType.BEARER)
        assert "Bearer authentication requires token" in str(exc_info.value)

    @pytest.mark.unit
    def test_auth_config_basic_auth(self):
        """Test auth config with basic authentication."""
        auth = AuthConfig(type=AuthType.BASIC, username="testuser", password="testpass")
        assert auth.type == AuthType.BASIC
        assert auth.username == "testuser"
        assert auth.password == "testpass"

    @pytest.mark.unit
    def test_auth_config_basic_missing_credentials(self):
        """Test auth config basic type requires username and password."""
        with pytest.raises(ValidationError) as exc_info:
            AuthConfig(type=AuthType.BASIC, username="testuser")
        assert "Basic authentication requires username and password" in str(
            exc_info.value
        )

    @pytest.mark.unit
    def test_auth_config_api_key(self):
        """Test auth config with API key."""
        auth = AuthConfig(type=AuthType.API_KEY, token="api-key-value")
        assert auth.type == AuthType.API_KEY
        assert auth.token == "api-key-value"


class TestCalendarSource:
    """Test CalendarSource model validation."""

    @pytest.mark.unit
    def test_calendar_source_valid(self):
        """Test valid calendar source."""
        source = CalendarSource(
            name="Test Calendar",
            url="https://example.com/calendar.ics",
            color="#FF0000",
            enabled=True,
            auth=AuthConfig(type=AuthType.NONE),
        )
        assert source.name == "Test Calendar"
        assert source.url == "https://example.com/calendar.ics"
        assert source.color == "#FF0000"
        assert source.enabled is True

    @pytest.mark.unit
    def test_calendar_source_invalid_url(self):
        """Test calendar source with invalid URL."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSource(
                name="Test Calendar",
                url="not-a-url",
                color="#FF0000",
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            )
        assert "URL validation failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_calendar_source_invalid_color_format(self):
        """Test calendar source with invalid color format."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSource(
                name="Test Calendar",
                url="https://example.com/calendar.ics",
                color="red",  # Invalid format
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            )
        assert "Color must be in hex format" in str(exc_info.value)

    @pytest.mark.unit
    def test_calendar_source_color_normalization(self):
        """Test calendar source color normalization."""
        source = CalendarSource(
            name="Test Calendar",
            url="https://example.com/calendar.ics",
            color="ff0000",  # Without #
            enabled=True,
            auth=AuthConfig(type=AuthType.NONE),
        )
        assert source.color == "#FF0000"

    @pytest.mark.unit
    def test_calendar_source_empty_name(self):
        """Test calendar source with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSource(
                name="",
                url="https://example.com/calendar.ics",
                color="#FF0000",
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            )
        assert "Name cannot be empty" in str(exc_info.value)


class TestManualEvent:
    """Test ManualEvent model validation."""

    @pytest.mark.unit
    def test_manual_event_valid(self):
        """Test valid manual event."""
        event = ManualEvent(
            title="Test Event",
            start=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            end=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
            location="Test Location",
            description="Test description",
        )
        assert event.title == "Test Event"
        assert event.start.tzinfo is not None
        assert event.end.tzinfo is not None

    @pytest.mark.unit
    def test_manual_event_end_before_start(self):
        """Test manual event with end before start."""
        with pytest.raises(ValidationError) as exc_info:
            ManualEvent(
                title="Test Event",
                start=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
                end=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
                location="Test Location",
            )
        assert "End time must be after start time" in str(exc_info.value)

    @pytest.mark.unit
    def test_manual_event_timezone_aware(self):
        """Test manual event requires timezone-aware datetimes."""
        with pytest.raises(ValidationError) as exc_info:
            ManualEvent(
                title="Test Event",
                start=datetime(2024, 1, 15, 10, 0),  # No timezone
                end=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
                location="Test Location",
            )
        assert "Datetime must be timezone-aware" in str(exc_info.value)


class TestEventModel:
    """Test EventModel validation."""

    @pytest.mark.unit
    def test_event_model_valid(self):
        """Test valid event model."""
        event = EventModel(
            original_uid="test@example.com",
            title="Test Event",
            start_time=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
            location="Test Location",
            description="Test description",
            source_name="Test Source",
            source_color="#FF0000",
            event_type=EventType.OTHER,
            status=EventStatus.CONFIRMED,
        )
        assert event.uid == "test@example.com"
        assert event.title == "Test Event"
        assert event.event_type == EventType.OTHER
        assert event.status == EventStatus.CONFIRMED

    @pytest.mark.unit
    def test_event_model_invalid_uid(self):
        """Test event model with invalid UID format."""
        with pytest.raises(ValidationError) as exc_info:
            EventModel(
                original_uid="invalid-uid",  # Missing @domain
                title="Test Event",
                start_time=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
                source_name="Test Source",
                source_color="#FF0000",
            )
        assert "UID must contain @ symbol" in str(exc_info.value)

    @pytest.mark.unit
    def test_event_model_end_before_start(self):
        """Test event model with end before start."""
        with pytest.raises(ValidationError) as exc_info:
            EventModel(
                original_uid="test@example.com",
                title="Test Event",
                start_time=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
                source_name="Test Source",
                source_color="#FF0000",
            )
        assert "End time must be after start time" in str(exc_info.value)


class TestDatabaseSettings:
    """Test DatabaseSettings validation."""

    @pytest.mark.unit
    def test_database_settings_sqlite_valid(self):
        """Test valid SQLite database URL."""
        settings = DatabaseSettings(url="sqlite+aiosqlite:///./test.db")
        assert settings.url == "sqlite+aiosqlite:///./test.db"
        assert settings.pool_size == 10

    @pytest.mark.unit
    def test_database_settings_postgresql_valid(self):
        """Test valid PostgreSQL database URL."""
        settings = DatabaseSettings(url="postgresql+asyncpg://user:pass@localhost/db")
        assert settings.url == "postgresql+asyncpg://user:pass@localhost/db"

    @pytest.mark.unit
    def test_database_settings_invalid_url(self):
        """Test invalid database URL."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(url="mysql://user:pass@localhost/db")
        assert "Database URL must be SQLite or PostgreSQL" in str(exc_info.value)

    @pytest.mark.unit
    def test_database_settings_pool_size_validation(self):
        """Test database pool size validation."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(pool_size=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)


class TestServerSettings:
    """Test ServerSettings validation."""

    @pytest.mark.unit
    def test_server_settings_valid(self):
        """Test valid server settings."""
        settings = ServerSettings(host="0.0.0.0", port=8000)
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

    @pytest.mark.unit
    def test_server_settings_invalid_port(self):
        """Test invalid server port."""
        with pytest.raises(ValidationError) as exc_info:
            ServerSettings(port=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ServerSettings(port=70000)
        assert "ensure this value is less than or equal to 65535" in str(exc_info.value)

    @pytest.mark.unit
    def test_server_settings_log_level_validation(self):
        """Test server log level validation."""
        settings = ServerSettings(log_level="DEBUG")
        assert settings.log_level == "debug"  # Normalized to lowercase

        with pytest.raises(ValidationError) as exc_info:
            ServerSettings(log_level="invalid")
        assert "Log level must be one of" in str(exc_info.value)


class TestCalendarSettings:
    """Test CalendarSettings validation."""

    @pytest.mark.unit
    def test_calendar_settings_valid(self):
        """Test valid calendar settings."""
        settings = CalendarSettings(
            config_file="config/calendars.yaml", fetch_timeout=30, cache_ttl=3600
        )
        assert settings.config_file.name == "calendars.yaml"
        assert settings.fetch_timeout == 30
        assert settings.cache_ttl == 3600

    @pytest.mark.unit
    def test_calendar_settings_invalid_config_file(self):
        """Test invalid configuration file extension."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSettings(config_file="config/calendars.json")
        assert "Configuration file must be YAML format" in str(exc_info.value)

    @pytest.mark.unit
    def test_calendar_settings_timeout_validation(self):
        """Test timeout validation."""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSettings(fetch_timeout=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)


class TestSecuritySettings:
    """Test SecuritySettings validation."""

    @pytest.mark.unit
    def test_security_settings_valid(self):
        """Test valid security settings."""
        settings = SecuritySettings(
            secret_key="a-very-long-secret-key-for-testing-purposes",
            cors_origins=["http://localhost:3000"],
        )
        assert len(settings.secret_key) >= 32
        assert settings.cors_origins == ["http://localhost:3000"]

    @pytest.mark.unit
    def test_security_settings_short_secret_key(self):
        """Test security settings with short secret key."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(secret_key="short")
        assert "Secret key must be at least 32 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_security_settings_rate_limit_validation(self):
        """Test rate limit validation."""
        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings(rate_limit_requests=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)


class TestSettings:
    """Test main Settings model."""

    @pytest.mark.unit
    def test_settings_valid(self):
        """Test valid settings configuration."""
        settings = Settings(app_name="Test App", environment="development")
        assert settings.app_name == "Test App"
        assert settings.environment == "development"
        assert settings.is_development is True
        assert settings.is_production is False

    @pytest.mark.unit
    def test_settings_invalid_environment(self):
        """Test invalid environment setting."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(environment="invalid")
        assert "Environment must be one of" in str(exc_info.value)

    @pytest.mark.unit
    def test_settings_production_flags(self):
        """Test production environment flags."""
        settings = Settings(environment="production")
        assert settings.is_production is True
        assert settings.is_development is False
