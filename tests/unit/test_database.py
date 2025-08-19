"""Async database tests with fixtures and transaction rollback."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.rallycal.database.operations import (
    CalendarSourceRepository,
    EventRepository,
    SyncHistoryRepository,
)
from src.rallycal.models.event import EventModel, EventStatus, EventType


class TestEventRepository:
    """Test EventRepository async database operations."""

    @pytest.fixture
    async def event_repo(self, test_db_session: AsyncSession):
        """Create EventRepository instance for testing."""
        return EventRepository(test_db_session)

    @pytest.fixture
    async def sample_event_data(self):
        """Create sample event data for testing."""
        return {
            "original_uid": "test-event@example.com",
            "title": "Test Event",
            "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            "location": "Test Location",
            "description": "Test description",
            "source_name": "Test Source",
            "source_color": "#FF0000",
            "event_type": EventType.OTHER,
            "status": EventStatus.CONFIRMED,
            "categories": ["Sports", "Soccer"],
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_event(self, event_repo: EventRepository, sample_event_data):
        """Test creating a new event."""
        event_model = EventModel(**sample_event_data)
        created_event = await event_repo.create_event(event_model)

        assert created_event.id is not None
        assert created_event.original_uid == sample_event_data["uid"]
        assert created_event.title == sample_event_data["title"]
        assert created_event.source_name == sample_event_data["source_name"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_event_by_uid(
        self, event_repo: EventRepository, sample_event_data
    ):
        """Test retrieving event by UID."""
        event_model = EventModel(**sample_event_data)
        created_event = await event_repo.create_event(event_model)

        retrieved_event = await event_repo.get_event_by_uid(sample_event_data["uid"])

        assert retrieved_event is not None
        assert retrieved_event.id == created_event.id
        assert retrieved_event.original_uid == sample_event_data["uid"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_nonexistent_event(self, event_repo: EventRepository):
        """Test retrieving non-existent event returns None."""
        retrieved_event = await event_repo.get_event_by_uid("nonexistent@example.com")
        assert retrieved_event is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_event(self, event_repo: EventRepository, sample_event_data):
        """Test updating an existing event."""
        event_model = EventModel(**sample_event_data)
        created_event = await event_repo.create_event(event_model)

        # Update the event
        updated_data = sample_event_data.copy()
        updated_data["title"] = "Updated Test Event"
        updated_data["description"] = "Updated description"

        updated_event_model = EventModel(**updated_data)
        result = await event_repo.update_event(created_event.original_uid, updated_event_model)

        assert result is not None
        assert result.title == "Updated Test Event"
        assert result.description == "Updated description"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_event(self, event_repo: EventRepository, sample_event_data):
        """Test deleting an event."""
        event_model = EventModel(**sample_event_data)
        created_event = await event_repo.create_event(event_model)

        # Delete the event
        deleted = await event_repo.delete_event(created_event.original_uid)
        assert deleted is True

        # Verify event is deleted
        retrieved_event = await event_repo.get_event_by_uid(sample_event_data["uid"])
        assert retrieved_event is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_events_by_date_range(self, event_repo: EventRepository):
        """Test retrieving events within a date range."""
        # Create multiple events with different dates
        base_date = datetime(2024, 1, 20, 10, 0, tzinfo=UTC)

        events_data = []
        for i in range(5):
            event_date = base_date.replace(day=20 + i)
            events_data.append(
                {
                    "original_uid": f"event-{i}@example.com",
                    "title": f"Event {i}",
                    "start_time": event_date,
                    "end_time": event_date.replace(hour=11),
                    "source_name": "Test Source",
                    "source_color": "#FF0000",
                }
            )

        # Create events
        for event_data in events_data:
            event_model = EventModel(**event_data)
            await event_repo.create_event(event_model)

        # Query events in date range
        start_date = base_date.replace(day=21)  # Second event
        end_date = base_date.replace(day=23)  # Fourth event

        events_in_range = await event_repo.get_events_by_date_range(
            start_date, end_date
        )

        assert len(events_in_range) == 3  # Events 1, 2, 3 (0-indexed)
        assert all(
            start_date <= event.start_time <= end_date for event in events_in_range
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_events_by_source(self, event_repo: EventRepository):
        """Test retrieving events by source name."""
        # Create events from different sources
        sources = ["Team A", "Team B", "Team C"]

        for i, source in enumerate(sources):
            event_data = {
                "original_uid": f"event-{i}@{source.lower().replace(' ', '-')}.com",
                "title": f"{source} Event",
                "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                "source_name": source,
                "source_color": "#FF0000",
            }
            event_model = EventModel(**event_data)
            await event_repo.create_event(event_model)

        # Query events from specific source
        team_a_events = await event_repo.get_events_by_source("Team A")

        assert len(team_a_events) == 1
        assert team_a_events[0].source_name == "Team A"
        assert team_a_events[0].title == "Team A Event"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bulk_create_events(self, event_repo: EventRepository):
        """Test bulk creation of events."""
        events_data = []
        for i in range(10):
            event_data = {
                "original_uid": f"bulk-event-{i}@example.com",
                "title": f"Bulk Event {i}",
                "start_time": datetime(2024, 1, 20, 10 + i, 0, tzinfo=UTC),
                "end_time": datetime(2024, 1, 20, 11 + i, 0, tzinfo=UTC),
                "source_name": "Bulk Source",
                "source_color": "#FF0000",
            }
            events_data.append(EventModel(**event_data))

        created_events = await event_repo.bulk_create_events(events_data)

        assert len(created_events) == 10
        assert all(event.id is not None for event in created_events)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_duplicate_uid_handling(
        self, event_repo: EventRepository, sample_event_data
    ):
        """Test handling of duplicate UIDs."""
        event_model = EventModel(**sample_event_data)

        # Create first event
        created_event1 = await event_repo.create_event(event_model)
        assert created_event1 is not None

        # Try to create event with same UID - should handle gracefully
        with pytest.raises(Exception):  # Should raise integrity error
            await event_repo.create_event(event_model)


class TestCalendarSourceRepository:
    """Test CalendarSourceRepository async database operations."""

    @pytest.fixture
    async def source_repo(self, test_db_session: AsyncSession):
        """Create CalendarSourceRepository instance for testing."""
        return CalendarSourceRepository(test_db_session)

    @pytest.fixture
    def sample_source_data(self):
        """Create sample calendar source data."""
        return {
            "name": "Test Calendar",
            "url": "https://example.com/test.ics",
            "color": "#FF0000",
            "enabled": True,
            "auth_type": "none",
            "auth_token": None,
            "auth_username": None,
            "auth_password": None,
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_calendar_source(
        self, source_repo: CalendarSourceRepository, sample_source_data
    ):
        """Test creating a calendar source."""
        created_source = await source_repo.create_source(sample_source_data)

        assert created_source.id is not None
        assert created_source.name == sample_source_data["name"]
        assert created_source.url == sample_source_data["url"]
        assert created_source.enabled is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_enabled_sources(self, source_repo: CalendarSourceRepository):
        """Test retrieving only enabled calendar sources."""
        # Create enabled and disabled sources
        enabled_source = {
            "name": "Enabled Calendar",
            "url": "https://example.com/enabled.ics",
            "color": "#FF0000",
            "enabled": True,
            "auth_type": "none",
        }

        disabled_source = {
            "name": "Disabled Calendar",
            "url": "https://example.com/disabled.ics",
            "color": "#00FF00",
            "enabled": False,
            "auth_type": "none",
        }

        await source_repo.create_source(enabled_source)
        await source_repo.create_source(disabled_source)

        enabled_sources = await source_repo.get_enabled_sources()

        assert len(enabled_sources) == 1
        assert enabled_sources[0].name == "Enabled Calendar"
        assert enabled_sources[0].enabled is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_source_enabled_status(
        self, source_repo: CalendarSourceRepository, sample_source_data
    ):
        """Test updating calendar source enabled status."""
        created_source = await source_repo.create_source(sample_source_data)

        # Disable the source
        updated_source = await source_repo.update_enabled_status(
            created_source.id, False
        )

        assert updated_source.enabled is False

        # Re-enable the source
        updated_source = await source_repo.update_enabled_status(
            created_source.id, True
        )

        assert updated_source.enabled is True


class TestSyncHistoryRepository:
    """Test SyncHistoryRepository async database operations."""

    @pytest.fixture
    async def sync_repo(self, test_db_session: AsyncSession):
        """Create SyncHistoryRepository instance for testing."""
        return SyncHistoryRepository(test_db_session)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_record_sync_attempt(self, sync_repo: SyncHistoryRepository):
        """Test recording a sync attempt."""
        sync_record = await sync_repo.record_sync_attempt(
            source_name="Test Source",
            status="success",
            events_count=5,
            duration_ms=1500.0,
            error_message=None,
        )

        assert sync_record.id is not None
        assert sync_record.source_name == "Test Source"
        assert sync_record.status == "success"
        assert sync_record.events_count == 5
        assert sync_record.duration_ms == 1500.0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_record_sync_failure(self, sync_repo: SyncHistoryRepository):
        """Test recording a failed sync attempt."""
        sync_record = await sync_repo.record_sync_attempt(
            source_name="Test Source",
            status="error",
            events_count=0,
            duration_ms=500.0,
            error_message="Connection timeout",
        )

        assert sync_record.status == "error"
        assert sync_record.events_count == 0
        assert sync_record.error_message == "Connection timeout"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_recent_sync_history(self, sync_repo: SyncHistoryRepository):
        """Test retrieving recent sync history."""
        # Create multiple sync records
        sources = ["Source A", "Source B", "Source C"]

        for source in sources:
            await sync_repo.record_sync_attempt(
                source_name=source, status="success", events_count=5, duration_ms=1000.0
            )

        recent_history = await sync_repo.get_recent_sync_history(limit=2)

        assert len(recent_history) == 2
        # Should be ordered by timestamp descending (most recent first)
        assert recent_history[0].timestamp >= recent_history[1].timestamp

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_sync_stats(self, sync_repo: SyncHistoryRepository):
        """Test retrieving sync statistics."""
        # Create successful and failed sync records
        await sync_repo.record_sync_attempt("Source A", "success", 10, 1000.0)
        await sync_repo.record_sync_attempt("Source A", "success", 8, 1200.0)
        await sync_repo.record_sync_attempt("Source A", "error", 0, 500.0, "Timeout")
        await sync_repo.record_sync_attempt("Source B", "success", 15, 800.0)

        stats = await sync_repo.get_sync_stats("Source A")

        assert stats["total_syncs"] == 3
        assert stats["successful_syncs"] == 2
        assert stats["failed_syncs"] == 1
        assert stats["success_rate"] == 2 / 3
        assert stats["avg_duration_ms"] == (1000.0 + 1200.0 + 500.0) / 3
        assert stats["avg_events_per_sync"] == (10 + 8 + 0) / 3


class TestDatabaseTransactions:
    """Test database transaction handling and rollback."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, test_db_session: AsyncSession):
        """Test that transactions are rolled back on errors."""
        repo = EventRepository(test_db_session)

        try:
            async with test_db_session.begin():
                # Create an event
                event_data = {
                    "original_uid": "test@example.com",
                    "title": "Test Event",
                    "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                    "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                    "source_name": "Test Source",
                    "source_color": "#FF0000",
                }
                event_model = EventModel(**event_data)
                await repo.create_event(event_model)

                # Raise an error to trigger rollback
                raise Exception("Simulated error")

        except Exception:
            pass  # Expected

        # Verify that the event was not committed
        retrieved_event = await repo.get_event_by_uid("test@example.com")
        assert retrieved_event is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_access(self, test_db_engine):
        """Test concurrent database access."""
        import asyncio

        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session = async_sessionmaker(test_db_engine, expire_on_commit=False)

        async def create_event(session_id: int):
            async with async_session() as session:
                repo = EventRepository(session)
                event_data = {
                    "original_uid": f"concurrent-{session_id}@example.com",
                    "title": f"Concurrent Event {session_id}",
                    "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                    "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                    "source_name": "Concurrent Source",
                    "source_color": "#FF0000",
                }
                event_model = EventModel(**event_data)
                return await repo.create_event(event_model)

        # Create events concurrently
        tasks = [create_event(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All events should be created successfully
        assert len(results) == 5
        assert all(result.id is not None for result in results)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_pooling(self, test_db_engine):
        """Test database connection pooling behavior."""

        async def get_connection_count():
            async with test_db_engine.connect() as conn:
                result = await conn.execute("PRAGMA database_list")
                return len(result.fetchall())

        # Test that multiple connections can be acquired
        connection_count = await get_connection_count()
        assert connection_count >= 1
