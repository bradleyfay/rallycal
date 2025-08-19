"""Pydantic models for calendar source configuration."""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


class AuthType(str, Enum):
    """Supported authentication types."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class AuthConfig(BaseModel):
    """Authentication configuration for calendar sources."""

    type: AuthType = Field(
        default=AuthType.NONE,
        description="Authentication type",
    )
    username: str | None = Field(
        default=None,
        description="Username for basic auth",
    )
    password: str | None = Field(
        default=None,
        description="Password for basic auth",
    )
    token: str | None = Field(
        default=None,
        description="Bearer token or API key",
    )
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header name for API key",
    )
    oauth2_client_id: str | None = Field(
        default=None,
        description="OAuth2 client ID",
    )
    oauth2_client_secret: str | None = Field(
        default=None,
        description="OAuth2 client secret",
    )
    oauth2_token_url: str | None = Field(
        default=None,
        description="OAuth2 token endpoint URL",
    )

    @validator("username")
    def validate_username_with_basic(
        cls, v: str | None, values: dict[str, Any]
    ) -> str | None:
        """Validate username is provided for basic auth."""
        if values.get("type") == AuthType.BASIC and not v:
            msg = "Username is required for basic authentication"
            raise ValueError(msg)
        return v

    @validator("password")
    def validate_password_with_basic(
        cls, v: str | None, values: dict[str, Any]
    ) -> str | None:
        """Validate password is provided for basic auth."""
        if values.get("type") == AuthType.BASIC and not v:
            msg = "Password is required for basic authentication"
            raise ValueError(msg)
        return v

    @validator("token")
    def validate_token_with_bearer_or_api_key(
        cls, v: str | None, values: dict[str, Any]
    ) -> str | None:
        """Validate token is provided for bearer or API key auth."""
        auth_type = values.get("type")
        if auth_type in {AuthType.BEARER, AuthType.API_KEY} and not v:
            msg = f"Token is required for {auth_type} authentication"
            raise ValueError(msg)
        return v

    @validator("oauth2_client_id")
    def validate_oauth2_client_id(
        cls, v: str | None, values: dict[str, Any]
    ) -> str | None:
        """Validate OAuth2 client ID is provided for OAuth2 auth."""
        if values.get("type") == AuthType.OAUTH2 and not v:
            msg = "OAuth2 client ID is required for OAuth2 authentication"
            raise ValueError(msg)
        return v

    @validator("oauth2_token_url")
    def validate_oauth2_token_url(
        cls, v: str | None, values: dict[str, Any]
    ) -> str | None:
        """Validate OAuth2 token URL is provided and valid for OAuth2 auth."""
        if values.get("type") == AuthType.OAUTH2:
            if not v:
                msg = "OAuth2 token URL is required for OAuth2 authentication"
                raise ValueError(msg)
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                msg = "OAuth2 token URL must be a valid URL"
                raise ValueError(msg)
        return v


class RecurrenceRule(BaseModel):
    """Recurrence rule for manual events."""

    frequency: Literal["daily", "weekly", "monthly", "yearly"] = Field(
        description="Recurrence frequency",
    )
    interval: int = Field(
        default=1,
        ge=1,
        le=365,
        description="Recurrence interval",
    )
    count: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description="Number of occurrences",
    )
    until: datetime | None = Field(
        default=None,
        description="End date for recurrence",
    )
    by_weekday: list[int] | None = Field(
        default=None,
        description="Weekdays for weekly recurrence (0=Monday, 6=Sunday)",
    )
    by_month_day: list[int] | None = Field(
        default=None,
        description="Days of month for monthly recurrence",
    )

    @validator("by_weekday")
    def validate_weekdays(cls, v: list[int] | None) -> list[int] | None:
        """Validate weekday values."""
        if v is not None:
            for day in v:
                if not 0 <= day <= 6:
                    msg = "Weekdays must be between 0 (Monday) and 6 (Sunday)"
                    raise ValueError(msg)
        return v

    @validator("by_month_day")
    def validate_month_days(cls, v: list[int] | None) -> list[int] | None:
        """Validate month day values."""
        if v is not None:
            for day in v:
                if not 1 <= day <= 31:
                    msg = "Month days must be between 1 and 31"
                    raise ValueError(msg)
        return v

    @validator("count")
    def validate_count_or_until(
        cls, v: int | None, values: dict[str, Any]
    ) -> int | None:
        """Validate that either count or until is specified, not both."""
        if v is not None and values.get("until") is not None:
            msg = "Cannot specify both count and until"
            raise ValueError(msg)
        return v


class ManualEvent(BaseModel):
    """Manual event configuration."""

    title: str = Field(
        min_length=1,
        max_length=255,
        description="Event title",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Event description",
    )
    start_date: datetime = Field(
        description="Event start date and time",
    )
    end_date: datetime = Field(
        description="Event end date and time",
    )
    location: str | None = Field(
        default=None,
        max_length=255,
        description="Event location",
    )
    all_day: bool = Field(
        default=False,
        description="Whether event is all day",
    )
    color: str | None = Field(
        default=None,
        description="Event color (hex format)",
    )
    recurrence: RecurrenceRule | None = Field(
        default=None,
        description="Recurrence rule for repeating events",
    )

    @validator("end_date")
    def validate_end_after_start(cls, v: datetime, values: dict[str, Any]) -> datetime:
        """Validate end date is after start date."""
        start_date = values.get("start_date")
        if start_date and v <= start_date:
            msg = "End date must be after start date"
            raise ValueError(msg)
        return v

    @validator("color")
    def validate_color_format(cls, v: str | None) -> str | None:
        """Validate color is in hex format."""
        if v is not None:
            if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                msg = "Color must be in hex format (#RRGGBB)"
                raise ValueError(msg)
        return v


class CalendarSource(BaseModel):
    """Configuration for a calendar source."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Display name for the calendar source",
    )
    url: str = Field(
        description="URL of the iCal/ICS feed",
    )
    color: str = Field(
        description="Color for events from this source (hex format)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this calendar source is enabled",
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description="Authentication configuration",
    )
    refresh_interval: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Refresh interval in seconds (5 minutes to 24 hours)",
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds",
    )
    retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for failed requests",
    )
    max_events: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of events to process",
    )
    filter_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords to filter events (include only events containing these)",
    )
    exclude_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords to exclude events (exclude events containing these)",
    )

    @validator("url")
    def validate_url_format(cls, v: str) -> str:
        """Validate URL format and scheme."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            msg = "URL must be a valid URL with scheme and netloc"
            raise ValueError(msg)
        if parsed.scheme not in {"http", "https", "webcal"}:
            msg = "URL scheme must be http, https, or webcal"
            raise ValueError(msg)
        return v

    @validator("color")
    def validate_color_format(cls, v: str) -> str:
        """Validate color is in hex format."""
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            msg = "Color must be in hex format (#RRGGBB)"
            raise ValueError(msg)
        return v

    @validator("name")
    def validate_name_uniqueness_placeholder(cls, v: str) -> str:
        """Placeholder for name uniqueness validation (handled at config level)."""
        return v


class CalendarConfig(BaseModel):
    """Complete calendar configuration."""

    calendars: list[CalendarSource] = Field(
        description="List of calendar sources",
    )
    manual_events: list[ManualEvent] = Field(
        default_factory=list,
        description="List of manual events",
    )
    global_settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Global configuration settings",
    )

    @validator("calendars")
    def validate_calendar_names_unique(
        cls, v: list[CalendarSource]
    ) -> list[CalendarSource]:
        """Validate that calendar names are unique."""
        names = [cal.name for cal in v]
        if len(names) != len(set(names)):
            msg = "Calendar names must be unique"
            raise ValueError(msg)
        return v

    @validator("calendars")
    def validate_calendar_urls_unique(
        cls, v: list[CalendarSource]
    ) -> list[CalendarSource]:
        """Validate that calendar URLs are unique."""
        urls = [cal.url for cal in v]
        if len(urls) != len(set(urls)):
            msg = "Calendar URLs must be unique"
            raise ValueError(msg)
        return v

    @validator("calendars")
    def validate_at_least_one_calendar(
        cls, v: list[CalendarSource]
    ) -> list[CalendarSource]:
        """Validate that at least one calendar is configured."""
        if not v:
            msg = "At least one calendar source must be configured"
            raise ValueError(msg)
        return v
