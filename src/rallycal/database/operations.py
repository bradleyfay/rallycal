"""Async repository pattern with comprehensive CRUD operations."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.logging import get_logger
from ..models.event import EventModel as EventPydantic
from .models import (
    Base,
    CalendarSourceModel,
    ConfigurationModel,
    EventModel,
    ManualEventModel,
    SyncHistoryModel,
)

logger = get_logger(__name__)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model_class: type[T]) -> None:
        """Initialize repository.

        Args:
            session: Database session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: UUID) -> T | None:
        """Get record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None
        """
        result = await self.session.get(self.model_class, id)
        return result

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> Sequence[T]:
        """Get all records with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by

        Returns:
            List of model instances
        """
        query = select(self.model_class)

        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by))

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records.

        Returns:
            Total count
        """
        query = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs) -> T:
        """Create new record.

        Args:
            **kwargs: Field values

        Returns:
            Created model instance
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> T | None:
        """Update record by ID.

        Args:
            id: Record ID
            **kwargs: Field values to update

        Returns:
            Updated model instance or None
        """
        query = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
            .returning(self.model_class)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        """Delete record by ID.

        Args:
            id: Record ID

        Returns:
            True if record was deleted
        """
        query = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def exists(self, id: UUID) -> bool:
        """Check if record exists.

        Args:
            id: Record ID

        Returns:
            True if record exists
        """
        query = (
            select(func.count())
            .select_from(self.model_class)
            .where(self.model_class.id == id)
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0


class CalendarSourceRepository(BaseRepository[CalendarSourceModel]):
    """Repository for calendar sources."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CalendarSourceModel)

    async def get_by_name(self, name: str) -> CalendarSourceModel | None:
        """Get calendar source by name.

        Args:
            name: Calendar source name

        Returns:
            Calendar source or None
        """
        query = select(CalendarSourceModel).where(CalendarSourceModel.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> CalendarSourceModel | None:
        """Get calendar source by URL.

        Args:
            url: Calendar source URL

        Returns:
            Calendar source or None
        """
        query = select(CalendarSourceModel).where(CalendarSourceModel.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_enabled(self) -> Sequence[CalendarSourceModel]:
        """Get all enabled calendar sources.

        Returns:
            List of enabled calendar sources
        """
        query = (
            select(CalendarSourceModel)
            .where(CalendarSourceModel.enabled == True)
            .order_by(CalendarSourceModel.name)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_due_for_sync(
        self, max_age_seconds: int = 3600
    ) -> Sequence[CalendarSourceModel]:
        """Get calendar sources that need syncing.

        Args:
            max_age_seconds: Maximum age of last sync in seconds

        Returns:
            List of calendar sources due for sync
        """
        cutoff_time = datetime.now(UTC).timestamp() - max_age_seconds
        cutoff_datetime = datetime.fromtimestamp(cutoff_time, UTC)

        query = (
            select(CalendarSourceModel)
            .where(
                and_(
                    CalendarSourceModel.enabled == True,
                    or_(
                        CalendarSourceModel.last_sync_at.is_(None),
                        CalendarSourceModel.last_sync_at < cutoff_datetime,
                    ),
                )
            )
            .order_by(CalendarSourceModel.last_sync_at.asc().nullsfirst())
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_sync_status(
        self,
        id: UUID,
        success: bool,
        error_message: str | None = None,
        etag: str | None = None,
        last_modified: datetime | None = None,
    ) -> CalendarSourceModel | None:
        """Update sync status for calendar source.

        Args:
            id: Calendar source ID
            success: Whether sync was successful
            error_message: Error message if sync failed
            etag: ETag from response
            last_modified: Last modified timestamp from response

        Returns:
            Updated calendar source or None
        """
        update_values = {
            "last_sync_at": datetime.now(UTC),
            "last_sync_success": success,
            "last_sync_error": error_message,
        }

        if etag:
            update_values["last_etag"] = etag

        if last_modified:
            update_values["last_modified"] = last_modified

        return await self.update(id, **update_values)

    async def get_with_recent_sync_history(
        self,
        limit: int = 10,
    ) -> Sequence[CalendarSourceModel]:
        """Get calendar sources with recent sync history.

        Args:
            limit: Number of sync history records to include

        Returns:
            Calendar sources with sync history
        """
        query = (
            select(CalendarSourceModel)
            .options(selectinload(CalendarSourceModel.sync_history).limit(limit))
            .order_by(CalendarSourceModel.name)
        )

        result = await self.session.execute(query)
        return result.scalars().all()


class EventRepository(BaseRepository[EventModel]):
    """Repository for calendar events."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventModel)

    async def get_by_source_and_uid(
        self,
        source_id: UUID,
        original_uid: str,
    ) -> EventModel | None:
        """Get event by source and original UID.

        Args:
            source_id: Calendar source ID
            original_uid: Original UID from source

        Returns:
            Event or None
        """
        query = select(EventModel).where(
            and_(
                EventModel.source_id == source_id,
                EventModel.original_uid == original_uid,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        source_ids: list[UUID] | None = None,
        exclude_duplicates: bool = True,
    ) -> Sequence[EventModel]:
        """Get events in time range.

        Args:
            start_time: Range start time
            end_time: Range end time
            source_ids: Optional list of source IDs to filter by
            exclude_duplicates: Whether to exclude duplicate events

        Returns:
            List of events in time range
        """
        query = select(EventModel).where(
            and_(EventModel.start_time >= start_time, EventModel.end_time <= end_time)
        )

        if source_ids:
            query = query.where(EventModel.source_id.in_(source_ids))

        if exclude_duplicates:
            query = query.where(EventModel.duplicate_of.is_(None))

        query = query.order_by(EventModel.start_time)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_upcoming_events(
        self,
        limit: int = 100,
        source_ids: list[UUID] | None = None,
        exclude_duplicates: bool = True,
    ) -> Sequence[EventModel]:
        """Get upcoming events.

        Args:
            limit: Maximum number of events to return
            source_ids: Optional list of source IDs to filter by
            exclude_duplicates: Whether to exclude duplicate events

        Returns:
            List of upcoming events
        """
        now = datetime.now(UTC)

        query = select(EventModel).where(EventModel.start_time > now)

        if source_ids:
            query = query.where(EventModel.source_id.in_(source_ids))

        if exclude_duplicates:
            query = query.where(EventModel.duplicate_of.is_(None))

        query = query.order_by(EventModel.start_time).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_content_hash(self, content_hash: str) -> Sequence[EventModel]:
        """Get events with matching content hash.

        Args:
            content_hash: Content hash to search for

        Returns:
            List of events with matching hash
        """
        query = select(EventModel).where(EventModel.content_hash == content_hash)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_duplicates(self, canonical_event_id: UUID) -> Sequence[EventModel]:
        """Get duplicate events for a canonical event.

        Args:
            canonical_event_id: ID of canonical event

        Returns:
            List of duplicate events
        """
        query = select(EventModel).where(EventModel.duplicate_of == canonical_event_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_as_duplicate(
        self,
        event_id: UUID,
        canonical_event_id: UUID,
    ) -> EventModel | None:
        """Mark event as duplicate of another event.

        Args:
            event_id: ID of duplicate event
            canonical_event_id: ID of canonical event

        Returns:
            Updated event or None
        """
        return await self.update(event_id, duplicate_of=canonical_event_id)

    async def bulk_create_events(
        self,
        events: list[EventPydantic],
        source_id: UUID,
    ) -> list[EventModel]:
        """Bulk create events from Pydantic models.

        Args:
            events: List of Pydantic event models
            source_id: Calendar source ID

        Returns:
            List of created database events
        """
        db_events = []

        for event in events:
            # Convert Pydantic model to database model
            db_event = EventModel(
                source_id=source_id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                timezone_name=event.timezone_name,
                location=event.location,
                source_name=event.source_name,
                source_url=event.source_url,
                original_uid=event.original_uid,
                color=event.color,
                event_type=event.event_type,
                tags=event.tags,
                status=event.status,
                sequence=event.sequence,
                last_modified=event.last_modified,
                last_fetched=event.last_fetched,
                content_hash=event.content_hash,
                duplicate_of=event.duplicate_of,
                recurrence_id=event.recurrence_id,
                recurrence_rule=event.recurrence_rule,
                metadata=event.metadata,
            )

            self.session.add(db_event)
            db_events.append(db_event)

        await self.session.flush()

        for db_event in db_events:
            await self.session.refresh(db_event)

        logger.info(f"Bulk created {len(db_events)} events")
        return db_events

    async def delete_by_source(self, source_id: UUID) -> int:
        """Delete all events from a specific source.

        Args:
            source_id: Calendar source ID

        Returns:
            Number of deleted events
        """
        query = delete(EventModel).where(EventModel.source_id == source_id)
        result = await self.session.execute(query)
        return result.rowcount

    async def cleanup_old_events(
        self,
        cutoff_date: datetime,
        exclude_source_ids: list[UUID] | None = None,
    ) -> int:
        """Clean up old events.

        Args:
            cutoff_date: Events before this date will be deleted
            exclude_source_ids: Source IDs to exclude from cleanup

        Returns:
            Number of deleted events
        """
        query = delete(EventModel).where(EventModel.end_time < cutoff_date)

        if exclude_source_ids:
            query = query.where(~EventModel.source_id.in_(exclude_source_ids))

        result = await self.session.execute(query)
        return result.rowcount


class SyncHistoryRepository(BaseRepository[SyncHistoryModel]):
    """Repository for sync history."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SyncHistoryModel)

    async def create_sync_record(
        self,
        calendar_source_id: UUID,
        **kwargs,
    ) -> SyncHistoryModel:
        """Create new sync history record.

        Args:
            calendar_source_id: Calendar source ID
            **kwargs: Additional sync data

        Returns:
            Created sync history record
        """
        return await self.create(calendar_source_id=calendar_source_id, **kwargs)

    async def get_by_source(
        self,
        calendar_source_id: UUID,
        limit: int = 50,
    ) -> Sequence[SyncHistoryModel]:
        """Get sync history for a calendar source.

        Args:
            calendar_source_id: Calendar source ID
            limit: Maximum number of records to return

        Returns:
            List of sync history records
        """
        query = (
            select(SyncHistoryModel)
            .where(SyncHistoryModel.calendar_source_id == calendar_source_id)
            .order_by(SyncHistoryModel.started_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_syncs(
        self,
        hours: int = 24,
        success_only: bool = False,
    ) -> Sequence[SyncHistoryModel]:
        """Get recent sync history.

        Args:
            hours: Number of hours to look back
            success_only: Whether to include only successful syncs

        Returns:
            List of recent sync history records
        """
        cutoff_time = datetime.now(UTC) - datetime.timedelta(hours=hours)

        query = select(SyncHistoryModel).where(
            SyncHistoryModel.started_at >= cutoff_time
        )

        if success_only:
            query = query.where(SyncHistoryModel.success == True)

        query = query.order_by(SyncHistoryModel.started_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def cleanup_old_history(
        self,
        retention_days: int = 90,
    ) -> int:
        """Clean up old sync history records.

        Args:
            retention_days: Number of days to retain

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.now(UTC) - datetime.timedelta(
            days=retention_days
        )

        query = delete(SyncHistoryModel).where(
            SyncHistoryModel.started_at < cutoff_date
        )
        result = await self.session.execute(query)
        return result.rowcount


class ManualEventRepository(BaseRepository[ManualEventModel]):
    """Repository for manual events."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ManualEventModel)

    async def get_enabled(self) -> Sequence[ManualEventModel]:
        """Get all enabled manual events.

        Returns:
            List of enabled manual events
        """
        query = (
            select(ManualEventModel)
            .where(ManualEventModel.enabled == True)
            .order_by(ManualEventModel.start_time)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Sequence[ManualEventModel]:
        """Get manual events in time range.

        Args:
            start_time: Range start time
            end_time: Range end time

        Returns:
            List of manual events in time range
        """
        query = (
            select(ManualEventModel)
            .where(
                and_(
                    ManualEventModel.enabled == True,
                    ManualEventModel.start_time >= start_time,
                    ManualEventModel.end_time <= end_time,
                )
            )
            .order_by(ManualEventModel.start_time)
        )

        result = await self.session.execute(query)
        return result.scalars().all()


class ConfigurationRepository(BaseRepository[ConfigurationModel]):
    """Repository for configuration management."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ConfigurationModel)

    async def get_active_config(self) -> ConfigurationModel | None:
        """Get the active configuration.

        Returns:
            Active configuration or None
        """
        query = (
            select(ConfigurationModel)
            .where(ConfigurationModel.is_active == True)
            .order_by(ConfigurationModel.version.desc())
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_new_version(
        self,
        config_data: dict[str, Any],
        config_hash: str,
        description: str | None = None,
        created_by: str | None = None,
    ) -> ConfigurationModel:
        """Create new configuration version.

        Args:
            config_data: Configuration data
            config_hash: Hash of configuration
            description: Optional description
            created_by: Who created this configuration

        Returns:
            Created configuration record
        """
        # Get next version number
        query = select(func.max(ConfigurationModel.version))
        result = await self.session.execute(query)
        max_version = result.scalar() or 0
        next_version = max_version + 1

        return await self.create(
            config_data=config_data,
            config_hash=config_hash,
            version=next_version,
            description=description,
            created_by=created_by,
        )

    async def activate_config(self, config_id: UUID) -> ConfigurationModel | None:
        """Activate a configuration version.

        Args:
            config_id: Configuration ID to activate

        Returns:
            Activated configuration or None
        """
        # Deactivate all configurations
        await self.session.execute(update(ConfigurationModel).values(is_active=False))

        # Activate the specified configuration
        return await self.update(
            config_id,
            is_active=True,
            applied_at=datetime.now(UTC),
        )
