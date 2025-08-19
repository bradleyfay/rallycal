"""Pydantic models for event data validation."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Event type classifications."""
    
    GAME = "game"
    PRACTICE = "practice"
    TOURNAMENT = "tournament"
    MEETING = "meeting"
    FUNDRAISER = "fundraiser"
    SOCIAL = "social"
    TRAVEL = "travel"
    OTHER = "other"


class EventStatus(str, Enum):
    """Event status values."""
    
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class EventModel(BaseModel):
    """Core event model for calendar events."""
    
    # Unique identifiers
    id: UUID = Field(
        default_factory=uuid4,
        description="Internal event ID",
    )
    original_uid: str | None = Field(
        default=None,
        description="Original UID from source calendar",
    )
    
    # Basic event information
    title: str = Field(
        min_length=1,
        max_length=255,
        description="Event title",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Event description",
    )
    
    # Date and time
    start_time: datetime = Field(
        description="Event start time",
    )
    end_time: datetime = Field(
        description="Event end time",
    )
    all_day: bool = Field(
        default=False,
        description="Whether event is all day",
    )
    timezone_name: str = Field(
        default="UTC",
        description="Event timezone",
    )
    
    # Location
    location: str | None = Field(
        default=None,
        max_length=255,
        description="Event location",
    )
    
    # Source information
    source_name: str = Field(
        description="Name of the calendar source",
    )
    source_url: str | None = Field(
        default=None,
        description="URL of the source calendar",
    )
    source_calendar_id: str | None = Field(
        default=None,
        description="ID of the source calendar",
    )
    
    # Visual and categorization
    color: str | None = Field(
        default=None,
        description="Event color (hex format)",
    )
    event_type: EventType | None = Field(
        default=None,
        description="Type of event",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Event tags for categorization",
    )
    
    # Status and metadata
    status: EventStatus = Field(
        default=EventStatus.CONFIRMED,
        description="Event status",
    )
    sequence: int = Field(
        default=0,
        ge=0,
        description="Sequence number for updates",
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When event was created in our system",
    )
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When event was last modified",
    )
    last_fetched: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When event was last fetched from source",
    )
    
    # Deduplication fields
    content_hash: str | None = Field(
        default=None,
        description="Hash of event content for deduplication",
    )
    duplicate_of: UUID | None = Field(
        default=None,
        description="ID of the canonical event if this is a duplicate",
    )
    
    # Recurrence information
    recurrence_id: str | None = Field(
        default=None,
        description="Recurrence ID for recurring events",
    )
    recurrence_rule: str | None = Field(
        default=None,
        description="RRULE string for recurring events",
    )
    
    # Additional metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from source",
    )
    
    class Config:
        """Pydantic model configuration."""
        
        # Use enum values in JSON
        use_enum_values = True
        
        # Validate assignment
        validate_assignment = True
        
        # Custom JSON encoders
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    @validator("end_time")
    def validate_end_after_start(cls, v: datetime, values: dict[str, Any]) -> datetime:
        """Validate end time is after start time."""
        start_time = values.get("start_time")
        if start_time and v <= start_time:
            msg = "End time must be after start time"
            raise ValueError(msg)
        return v
    
    @validator("color")
    def validate_color_format(cls, v: str | None) -> str | None:
        """Validate color is in hex format."""
        if v is not None:
            import re
            if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                msg = "Color must be in hex format (#RRGGBB)"
                raise ValueError(msg)
        return v
    
    @validator("tags")
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        # Remove empty tags and strip whitespace
        cleaned_tags = [tag.strip() for tag in v if tag.strip()]
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        return unique_tags
    
    @validator("start_time", "end_time", "created_at", "last_modified", "last_fetched")
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime objects are timezone-aware."""
        if v.tzinfo is None:
            # Assume UTC if no timezone provided
            return v.replace(tzinfo=timezone.utc)
        return v
    
    def is_duplicate(self) -> bool:
        """Check if this event is marked as a duplicate."""
        return self.duplicate_of is not None
    
    def is_recurring(self) -> bool:
        """Check if this event is part of a recurring series."""
        return self.recurrence_rule is not None or self.recurrence_id is not None
    
    def is_past(self) -> bool:
        """Check if this event is in the past."""
        return self.end_time < datetime.now(timezone.utc)
    
    def is_upcoming(self) -> bool:
        """Check if this event is upcoming (starts in the future)."""
        return self.start_time > datetime.now(timezone.utc)
    
    def is_current(self) -> bool:
        """Check if this event is currently happening."""
        now = datetime.now(timezone.utc)
        return self.start_time <= now <= self.end_time
    
    def get_duration_minutes(self) -> int:
        """Get event duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def update_hash(self) -> None:
        """Update the content hash for deduplication."""
        import hashlib
        
        # Create hash based on key fields
        hash_content = (
            f"{self.title}{self.start_time}{self.end_time}"
            f"{self.location or ''}{self.description or ''}"
        )
        self.content_hash = hashlib.md5(hash_content.encode()).hexdigest()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        return self.dict(
            exclude_none=True,
            by_alias=True,
        )


class EventCreate(BaseModel):
    """Model for creating new events."""
    
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_time: datetime
    end_time: datetime
    all_day: bool = Field(default=False)
    location: str | None = Field(default=None, max_length=255)
    source_name: str
    color: str | None = Field(default=None)
    event_type: EventType | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @validator("end_time")
    def validate_end_after_start(cls, v: datetime, values: dict[str, Any]) -> datetime:
        """Validate end time is after start time."""
        start_time = values.get("start_time")
        if start_time and v <= start_time:
            msg = "End time must be after start time"
            raise ValueError(msg)
        return v


class EventUpdate(BaseModel):
    """Model for updating existing events."""
    
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    start_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    all_day: bool | None = Field(default=None)
    location: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None)
    event_type: EventType | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    status: EventStatus | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)