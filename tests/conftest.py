"""Pytest configuration and shared fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator, Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_session() -> AsyncGenerator[None, None]:
    """Provide an async session for database tests."""
    # Will be implemented when database layer is added
    yield


@pytest.fixture
def sample_calendar_config():
    """Provide sample calendar configuration for tests."""
    return {
        "calendars": [
            {
                "name": "Team A Schedule",
                "url": "https://example.com/team-a.ics",
                "color": "#FF0000",
                "enabled": True
            },
            {
                "name": "Team B Schedule", 
                "url": "https://example.com/team-b.ics",
                "color": "#00FF00",
                "enabled": True
            }
        ]
    }


@pytest.fixture
def sample_ical_data():
    """Provide sample iCal data for testing."""
    return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test Calendar//EN
BEGIN:VEVENT
UID:test-event-1@example.com
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
SUMMARY:Sample Event
DESCRIPTION:Test event description
LOCATION:Test Location
END:VEVENT
END:VCALENDAR"""