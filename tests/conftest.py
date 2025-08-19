"""Pytest configuration and shared fixtures."""

import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.rallycal.api.main import app
from src.rallycal.core.settings import Settings
from src.rallycal.database.models import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test application settings."""
    return Settings(
        app_name="RallyCal Test",
        app_version="0.1.0-test",
        debug=True,
        environment="testing",
        database={"url": "sqlite+aiosqlite:///:memory:"},
        server={"host": "127.0.0.1", "port": 8001},
        calendar={"cache_ttl": 60, "fetch_timeout": 5},
        security={"secret_key": "test-secret-key-for-testing-only"},
    )


@pytest.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession]:
    """Provide test database session with transaction rollback."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient]:
    """Provide test HTTP client for FastAPI integration tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_calendar_config():
    """Provide sample calendar configuration for tests."""
    return {
        "calendars": [
            {
                "name": "Team A Schedule",
                "url": "https://example.com/team-a.ics",
                "color": "#FF0000",
                "enabled": True,
                "auth": {"type": "none"},
            },
            {
                "name": "Team B Schedule",
                "url": "https://example.com/team-b.ics",
                "color": "#00FF00",
                "enabled": True,
                "auth": {"type": "bearer", "token": "test-token"},
            },
            {
                "name": "Disabled Calendar",
                "url": "https://example.com/disabled.ics",
                "color": "#0000FF",
                "enabled": False,
                "auth": {"type": "none"},
            },
        ],
        "manual_events": [
            {
                "title": "Manual Event",
                "start": "2024-01-15T10:00:00Z",
                "end": "2024-01-15T11:00:00Z",
                "location": "Test Location",
                "description": "Test manual event",
            }
        ],
    }


@pytest.fixture
def sample_ical_data():
    """Provide sample iCal data for testing."""
    return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:20240310T070000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:20241103T060000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
UID:test-event-1@example.com
DTSTART;TZID=America/New_York:20240120T100000
DTEND;TZID=America/New_York:20240120T110000
SUMMARY:Sample Event
DESCRIPTION:Test event description
LOCATION:Test Location
CATEGORIES:Sports,Soccer
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:test-event-2@example.com
DTSTART;TZID=America/New_York:20240121T140000
DTEND;TZID=America/New_York:20240121T150000
SUMMARY:Another Event
DESCRIPTION:Another test event
LOCATION:Another Location
CATEGORIES:Sports,Basketball
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""


@pytest.fixture
def mock_httpx_client():
    """Provide mock httpx client for HTTP requests."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/calendar"}
    mock_response.text = "mock ical data"
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_events():
    """Provide sample event data for testing."""
    return [
        {
            "uid": "event-1@example.com",
            "title": "Soccer Practice",
            "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            "location": "Soccer Field",
            "description": "Weekly soccer practice",
            "source_name": "Team A",
            "source_color": "#FF0000",
            "categories": ["Sports", "Soccer"],
        },
        {
            "uid": "event-2@example.com",
            "title": "Basketball Game",
            "start_time": datetime(2024, 1, 21, 14, 0, tzinfo=UTC),
            "end_time": datetime(2024, 1, 21, 15, 30, tzinfo=UTC),
            "location": "Gym",
            "description": "Championship game",
            "source_name": "Team B",
            "source_color": "#00FF00",
            "categories": ["Sports", "Basketball"],
        },
    ]


@pytest.fixture
def duplicate_events():
    """Provide duplicate event data for deduplication testing."""
    return [
        {
            "uid": "different-uid-1@example.com",
            "title": "Soccer Practice",
            "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=UTC),
            "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            "location": "Soccer Field",
            "source_name": "Team A",
        },
        {
            "uid": "different-uid-2@example.com",
            "title": "Soccer Practice",  # Same title
            "start_time": datetime(
                2024, 1, 20, 10, 0, tzinfo=UTC
            ),  # Same time
            "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            "location": "Soccer Field",  # Same location
            "source_name": "Team B",  # Different source
        },
    ]
