"""Unit tests for event processing and duplicate detection validation."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from src.rallycal.config.models import AuthConfig, AuthType, CalendarSource
from src.rallycal.models.event import EventModel
from src.rallycal.services.processor import EventProcessor
from src.rallycal.utils.color_manager import ColorManager
from src.rallycal.utils.deduplicator import EventDeduplicator


class TestEventProcessor:
    """Test EventProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create EventProcessor instance for testing."""
        return EventProcessor()

    @pytest.fixture
    def sample_calendar_sources(self):
        """Create sample calendar sources."""
        return [
            CalendarSource(
                name="Team A",
                url="https://example.com/team-a.ics",
                color="#FF0000",
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            ),
            CalendarSource(
                name="Team B",
                url="https://example.com/team-b.ics",
                color="#00FF00",
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            ),
        ]

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        return [
            EventModel(
                original_uid="event1@team-a.com",
                title="Soccer Practice",
                start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                location="Soccer Field A",
                description="Weekly practice",
                source_name="Team A",
                source_color="#FF0000",
                categories=["Sports", "Soccer"],
            ),
            EventModel(
                original_uid="event2@team-b.com",
                title="Basketball Game",
                start_time=datetime(2024, 1, 21, 14, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 21, 15, 30, tzinfo=UTC),
                location="Gym",
                description="Championship game",
                source_name="Team B",
                source_color="#00FF00",
                categories=["Sports", "Basketball"],
            ),
        ]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_events_basic(self, processor, sample_events):
        """Test basic event processing."""
        with patch.object(
            processor, "_fetch_all_calendars", return_value=sample_events
        ):
            processed_events = await processor.process_all_events()

            assert len(processed_events) == 2
            assert processed_events[0].title == "Soccer Practice"
            assert processed_events[1].title == "Basketball Game"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_title_formatting(self, processor, sample_events):
        """Test event title formatting with source identification."""
        with patch.object(
            processor, "_fetch_all_calendars", return_value=sample_events
        ):
            processed_events = await processor.process_all_events(
                include_source_prefix=True
            )

            assert processed_events[0].title == "[Team A] Soccer Practice"
            assert processed_events[1].title == "[Team B] Basketball Game"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_color_assignment_consistency(self, processor):
        """Test deterministic color assignment."""
        events = [
            EventModel(
                original_uid="event1@example.com",
                title="Test Event",
                start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                source_name="Test Source",
                source_color="#FF0000",
            )
        ]

        with patch.object(processor, "_fetch_all_calendars", return_value=events):
            processed1 = await processor.process_all_events()
            processed2 = await processor.process_all_events()

            # Color should be consistent across runs
            assert processed1[0].source_color == processed2[0].source_color

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_disabled_calendar_filtering(self, processor):
        """Test that disabled calendars are filtered out."""
        disabled_source = CalendarSource(
            name="Disabled Calendar",
            url="https://example.com/disabled.ics",
            color="#0000FF",
            enabled=False,
            auth=AuthConfig(type=AuthType.NONE),
        )

        with patch.object(processor, "config_manager") as mock_config:
            mock_config.get_calendar_sources.return_value = [disabled_source]

            processed_events = await processor.process_all_events()

            # Should return empty list since calendar is disabled
            assert len(processed_events) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_conflict_resolution(self, processor):
        """Test conflict resolution for overlapping events."""
        conflicting_events = [
            EventModel(
                original_uid="event1@example.com",
                title="Soccer Practice",
                start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
                location="Field A",
                source_name="Team A",
                source_color="#FF0000",
            ),
            EventModel(
                original_uid="event2@example.com",
                title="Soccer Game",
                start_time=datetime(2024, 1, 20, 10, 30, tzinfo=UTC),
                end_time=datetime(2024, 1, 20, 11, 30, tzinfo=UTC),
                location="Field A",
                source_name="Team B",
                source_color="#00FF00",
            ),
        ]

        with patch.object(
            processor, "_fetch_all_calendars", return_value=conflicting_events
        ):
            processed_events = await processor.process_all_events()

            # Both events should be preserved but marked as conflicting
            assert len(processed_events) == 2
            # Events should have conflict markers in description or title
            descriptions = [event.description for event in processed_events]
            assert any("CONFLICT" in desc for desc in descriptions if desc)


class TestEventDeduplicator:
    """Test EventDeduplicator functionality."""

    @pytest.fixture
    def deduplicator(self):
        """Create EventDeduplicator instance."""
        return EventDeduplicator()

    @pytest.mark.unit
    def test_exact_duplicate_detection(self, deduplicator):
        """Test detection of exact duplicate events."""
        event1 = EventModel(
            original_uid="different-uid-1@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="different-uid-2@example.com",
            title="Soccer Practice",  # Same title
            start_time=datetime(
                2024, 1, 20, 10, 0, tzinfo=UTC
            ),  # Same time
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",  # Same location
            source_name="Team B",
            source_color="#00FF00",
        )

        events = [event1, event2]
        deduplicated = deduplicator.deduplicate_events(events)

        # Should keep only one event
        assert len(deduplicated) == 1
        # Should prefer the first event encountered
        assert deduplicated[0].source_name == "Team A"

    @pytest.mark.unit
    def test_fuzzy_title_matching(self, deduplicator):
        """Test fuzzy matching for similar titles."""
        event1 = EventModel(
            original_uid="event1@example.com",
            title="Soccer Practice - Team A",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="event2@example.com",
            title="Soccer Practice Team A",  # Similar but not identical
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            source_name="Team B",
            source_color="#00FF00",
        )

        events = [event1, event2]
        deduplicated = deduplicator.deduplicate_events(events, fuzzy_threshold=0.8)

        # Should detect as duplicates due to high similarity
        assert len(deduplicated) == 1

    @pytest.mark.unit
    def test_time_window_tolerance(self, deduplicator):
        """Test time window tolerance for near-duplicate events."""
        event1 = EventModel(
            original_uid="event1@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="event2@example.com",
            title="Soccer Practice",
            start_time=datetime(
                2024, 1, 20, 10, 5, tzinfo=UTC
            ),  # 5 min later
            end_time=datetime(2024, 1, 20, 11, 5, tzinfo=UTC),
            location="Soccer Field",
            source_name="Team B",
            source_color="#00FF00",
        )

        events = [event1, event2]

        # With 10-minute tolerance, should be considered duplicates
        deduplicated = deduplicator.deduplicate_events(
            events, time_tolerance_minutes=10
        )
        assert len(deduplicated) == 1

        # With 2-minute tolerance, should be considered different
        deduplicated = deduplicator.deduplicate_events(events, time_tolerance_minutes=2)
        assert len(deduplicated) == 2

    @pytest.mark.unit
    def test_location_normalization(self, deduplicator):
        """Test location normalization for duplicate detection."""
        event1 = EventModel(
            original_uid="event1@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field #1",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="event2@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="soccer field #1",  # Different case and formatting
            source_name="Team B",
            source_color="#00FF00",
        )

        events = [event1, event2]
        deduplicated = deduplicator.deduplicate_events(events)

        # Should be considered duplicates after location normalization
        assert len(deduplicated) == 1

    @pytest.mark.unit
    def test_preserve_most_detailed_event(self, deduplicator):
        """Test that the most detailed event is preserved in deduplication."""
        event1 = EventModel(
            original_uid="event1@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            description="Basic practice",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="event2@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field",
            description="Detailed practice session with drills, scrimmage, and team meeting",
            source_name="Team B",
            source_color="#00FF00",
            categories=["Sports", "Soccer", "Training"],
        )

        events = [event1, event2]
        deduplicated = deduplicator.deduplicate_events(events)

        # Should preserve the more detailed event (event2)
        assert len(deduplicated) == 1
        assert deduplicated[0].source_name == "Team B"
        assert len(deduplicated[0].categories) == 3

    @pytest.mark.unit
    def test_different_events_preserved(self, deduplicator):
        """Test that genuinely different events are preserved."""
        event1 = EventModel(
            original_uid="event1@example.com",
            title="Soccer Practice",
            start_time=datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            location="Soccer Field A",
            source_name="Team A",
            source_color="#FF0000",
        )

        event2 = EventModel(
            original_uid="event2@example.com",
            title="Basketball Game",  # Different sport
            start_time=datetime(
                2024, 1, 20, 14, 0, tzinfo=UTC
            ),  # Different time
            end_time=datetime(2024, 1, 20, 15, 0, tzinfo=UTC),
            location="Gym",  # Different location
            source_name="Team B",
            source_color="#00FF00",
        )

        events = [event1, event2]
        deduplicated = deduplicator.deduplicate_events(events)

        # Both events should be preserved
        assert len(deduplicated) == 2


class TestColorManager:
    """Test ColorManager functionality."""

    @pytest.fixture
    def color_manager(self):
        """Create ColorManager instance."""
        return ColorManager()

    @pytest.mark.unit
    def test_consistent_color_assignment(self, color_manager):
        """Test that the same source gets the same color consistently."""
        color1 = color_manager.get_color_for_source("Team A")
        color2 = color_manager.get_color_for_source("Team A")

        assert color1 == color2

    @pytest.mark.unit
    def test_different_sources_different_colors(self, color_manager):
        """Test that different sources get different colors."""
        color_a = color_manager.get_color_for_source("Team A")
        color_b = color_manager.get_color_for_source("Team B")

        assert color_a != color_b

    @pytest.mark.unit
    def test_custom_color_preference(self, color_manager):
        """Test that custom colors are preferred over generated ones."""
        custom_color = "#FF0000"
        assigned_color = color_manager.get_color_for_source(
            "Team A", preferred_color=custom_color
        )

        assert assigned_color == custom_color

    @pytest.mark.unit
    def test_color_validation(self, color_manager):
        """Test color validation and normalization."""
        # Test various color formats
        assert color_manager.validate_color("#FF0000") == "#FF0000"
        assert color_manager.validate_color("ff0000") == "#FF0000"
        assert color_manager.validate_color("#f00") == "#FF0000"

        # Test invalid colors
        with pytest.raises(ValueError):
            color_manager.validate_color("invalid")

        with pytest.raises(ValueError):
            color_manager.validate_color("#gggggg")

    @pytest.mark.unit
    def test_color_contrast_checking(self, color_manager):
        """Test color contrast validation for accessibility."""
        # Light colors should have good contrast with dark text
        assert color_manager.has_good_contrast("#FFFFFF", "#000000")

        # Dark colors should have good contrast with light text
        assert color_manager.has_good_contrast("#000000", "#FFFFFF")

        # Similar colors should have poor contrast
        assert not color_manager.has_good_contrast("#AAAAAA", "#BBBBBB")
