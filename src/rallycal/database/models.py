"""SQLAlchemy async models for database persistence."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..models.event import EventStatus, EventType


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""

    # Use UUID for PostgreSQL, String for SQLite
    type_annotation_map = {
        UUID: PG_UUID(as_uuid=True),
    }


class CalendarSourceModel(Base):
    """Database model for calendar sources."""

    __tablename__ = "calendar_sources"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # #RRGGBB
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Configuration
    refresh_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_events: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)

    # Authentication (stored as JSON)
    auth_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Filtering
    filter_keywords: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    exclude_keywords: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Sync tracking
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Caching
    last_etag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    events: Mapped[list["EventModel"]] = relationship(
        "EventModel",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    sync_history: Mapped[list["SyncHistoryModel"]] = relationship(
        "SyncHistoryModel",
        back_populates="calendar_source",
        cascade="all, delete-orphan",
        order_by="SyncHistoryModel.created_at.desc()",
    )

    # Indexes
    __table_args__ = (
        Index("idx_calendar_sources_enabled", "enabled"),
        Index("idx_calendar_sources_last_sync", "last_sync_at"),
    )

    def __repr__(self) -> str:
        return f"<CalendarSource(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class EventModel(Base):
    """Database model for calendar events."""

    __tablename__ = "events"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign key to calendar source
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Basic event information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Date and time
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timezone_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC"
    )

    # Location
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Source information
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_uid: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Visual and categorization
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # #RRGGBB
    event_type: Mapped[EventType | None] = mapped_column(
        Enum(EventType),
        nullable=True,
    )
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Status and metadata
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus),
        nullable=False,
        default=EventStatus.CONFIRMED,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_fetched: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Deduplication fields
    content_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duplicate_of: Mapped[UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Recurrence information
    recurrence_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional metadata
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    source: Mapped["CalendarSourceModel"] = relationship(
        "CalendarSourceModel",
        back_populates="events",
    )

    # Self-referential relationship for duplicates
    canonical_event: Mapped["EventModel | None"] = relationship(
        "EventModel",
        remote_side=[id],
        back_populates="duplicates",
    )
    duplicates: Mapped[list["EventModel"]] = relationship(
        "EventModel",
        back_populates="canonical_event",
    )

    # Indexes for performance
    __table_args__ = (
        # Time-based queries
        Index("idx_events_start_time", "start_time"),
        Index("idx_events_end_time", "end_time"),
        Index("idx_events_time_range", "start_time", "end_time"),
        # Source queries
        Index("idx_events_source_id", "source_id"),
        Index("idx_events_source_name", "source_name"),
        # Deduplication
        Index("idx_events_content_hash", "content_hash"),
        Index("idx_events_duplicate_of", "duplicate_of"),
        Index("idx_events_original_uid", "original_uid"),
        # Status and type queries
        Index("idx_events_status", "status"),
        Index("idx_events_event_type", "event_type"),
        # Composite indexes for common queries
        Index("idx_events_source_time", "source_id", "start_time"),
        Index("idx_events_status_time", "status", "start_time"),
        Index("idx_events_future_events", "start_time", "status"),
        # Unique constraint for original UID per source
        UniqueConstraint(
            "source_id", "original_uid", name="uq_events_source_original_uid"
        ),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', start={self.start_time})>"


class SyncHistoryModel(Base):
    """Database model for calendar sync history."""

    __tablename__ = "sync_history"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign key to calendar source
    calendar_source_id: Mapped[UUID] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Sync information
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Results
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Statistics
    events_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_added: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # HTTP response information
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_etag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Performance metrics
    fetch_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parse_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional details
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    calendar_source: Mapped["CalendarSourceModel"] = relationship(
        "CalendarSourceModel",
        back_populates="sync_history",
    )

    # Indexes
    __table_args__ = (
        Index("idx_sync_history_calendar_source", "calendar_source_id"),
        Index("idx_sync_history_started_at", "started_at"),
        Index("idx_sync_history_success", "success"),
        Index("idx_sync_history_source_time", "calendar_source_id", "started_at"),
    )

    @property
    def duration_seconds(self) -> float | None:
        """Get sync duration in seconds."""
        if self.total_duration_ms is not None:
            return self.total_duration_ms / 1000.0
        elif self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __repr__(self) -> str:
        return f"<SyncHistory(id={self.id}, source_id={self.calendar_source_id}, success={self.success})>"


class ManualEventModel(Base):
    """Database model for manually created events."""

    __tablename__ = "manual_events"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Basic event information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Date and time
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timezone_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC"
    )

    # Location
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Visual
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # #RRGGBB

    # Recurrence
    recurrence_rule: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Metadata
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Indexes
    __table_args__ = (
        Index("idx_manual_events_start_time", "start_time"),
        Index("idx_manual_events_enabled", "enabled"),
        Index("idx_manual_events_time_range", "start_time", "end_time"),
    )

    def __repr__(self) -> str:
        return f"<ManualEvent(id={self.id}, title='{self.title}', start={self.start_time})>"


class ConfigurationModel(Base):
    """Database model for storing configuration snapshots."""

    __tablename__ = "configurations"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Configuration data
    config_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Version information
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Indexes
    __table_args__ = (
        Index("idx_configurations_version", "version"),
        Index("idx_configurations_is_active", "is_active"),
        Index("idx_configurations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Configuration(id={self.id}, version={self.version}, active={self.is_active})>"
