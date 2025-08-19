"""Unit tests for async calendar fetching with httpx mock responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from src.rallycal.config.models import AuthConfig, AuthType, CalendarSource
from src.rallycal.services.fetcher import (
    AuthenticationError,
    CalendarFetcher,
    CalendarFetchError,
    ParsingError,
    TimeoutError,
)


class TestCalendarFetcher:
    """Test CalendarFetcher async operations."""

    @pytest.fixture
    def fetcher(self):
        """Create CalendarFetcher instance for testing."""
        return CalendarFetcher(
            max_connections=5,
            max_keepalive_connections=2,
            keepalive_expiry=10.0,
            default_timeout=10.0,
        )

    @pytest.fixture
    def sample_calendar_source(self):
        """Create sample calendar source for testing."""
        return CalendarSource(
            name="Test Calendar",
            url="https://example.com/test.ics",
            color="#FF0000",
            enabled=True,
            auth=AuthConfig(type=AuthType.NONE),
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_success(
        self, fetcher, sample_calendar_source, sample_ical_data
    ):
        """Test successful calendar fetch."""
        with patch.object(fetcher, "_client") as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}
            mock_response.text = sample_ical_data
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            # Fetch calendar
            events = await fetcher.fetch_calendar(sample_calendar_source)

            # Verify request was made correctly
            mock_client.get.assert_called_once_with(
                "https://example.com/test.ics", timeout=10.0, headers={}
            )

            # Verify events were parsed
            assert len(events) == 2
            assert events[0].title == "Sample Event"
            assert events[1].title == "Another Event"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_with_bearer_auth(self, fetcher):
        """Test calendar fetch with bearer token authentication."""
        source = CalendarSource(
            name="Authenticated Calendar",
            url="https://example.com/auth.ics",
            color="#FF0000",
            enabled=True,
            auth=AuthConfig(type=AuthType.BEARER, token="test-token"),
        )

        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            await fetcher.fetch_calendar(source)

            # Verify authorization header was included
            call_args = mock_client.get.call_args
            assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_with_basic_auth(self, fetcher):
        """Test calendar fetch with basic authentication."""
        source = CalendarSource(
            name="Basic Auth Calendar",
            url="https://example.com/basic.ics",
            color="#FF0000",
            enabled=True,
            auth=AuthConfig(
                type=AuthType.BASIC, username="testuser", password="testpass"
            ),
        )

        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            await fetcher.fetch_calendar(source)

            # Verify auth parameter was passed
            call_args = mock_client.get.call_args
            assert call_args[1]["auth"] == ("testuser", "testpass")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_http_error(self, fetcher, sample_calendar_source):
        """Test calendar fetch with HTTP error."""
        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )

            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(CalendarFetchError) as exc_info:
                await fetcher.fetch_calendar(sample_calendar_source)

            assert "HTTP error 404" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_timeout(self, fetcher, sample_calendar_source):
        """Test calendar fetch with timeout."""
        with patch.object(fetcher, "_client") as mock_client:
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(TimeoutError) as exc_info:
                await fetcher.fetch_calendar(sample_calendar_source)

            assert "Request timed out" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_authentication_error(
        self, fetcher, sample_calendar_source
    ):
        """Test calendar fetch with authentication error."""
        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            )

            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(AuthenticationError) as exc_info:
                await fetcher.fetch_calendar(sample_calendar_source)

            assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_invalid_ical(self, fetcher, sample_calendar_source):
        """Test calendar fetch with invalid iCal data."""
        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "This is not valid iCal data"
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(ParsingError) as exc_info:
                await fetcher.fetch_calendar(sample_calendar_source)

            assert "Failed to parse calendar data" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_with_etag_caching(
        self, fetcher, sample_calendar_source
    ):
        """Test calendar fetch with ETag caching."""
        with patch.object(fetcher, "_client") as mock_client:
            # First request - return data with ETag
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {
                "content-type": "text/calendar",
                "etag": '"test-etag"',
            }
            mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            # First fetch
            events1 = await fetcher.fetch_calendar(sample_calendar_source)

            # Second fetch should include If-None-Match header
            events2 = await fetcher.fetch_calendar(sample_calendar_source)

            # Verify second request included caching header
            assert mock_client.get.call_count == 2
            second_call_headers = mock_client.get.call_args_list[1][1]["headers"]
            assert second_call_headers.get("If-None-Match") == '"test-etag"'

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_304_not_modified(
        self, fetcher, sample_calendar_source
    ):
        """Test calendar fetch with 304 Not Modified response."""
        with patch.object(fetcher, "_client") as mock_client:
            # Setup cache
            fetcher._cache["https://example.com/test.ics"] = {
                "etag": '"test-etag"',
                "events": [],
            }

            # Mock 304 response
            mock_response = MagicMock()
            mock_response.status_code = 304
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            events = await fetcher.fetch_calendar(sample_calendar_source)

            # Should return cached events
            assert events == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_calendar_with_retry(self, fetcher, sample_calendar_source):
        """Test calendar fetch with retry logic."""
        with patch.object(fetcher, "_client") as mock_client:
            # First call fails, second succeeds
            failure_response = MagicMock()
            failure_response.status_code = 500
            failure_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=failure_response
            )

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            success_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(
                side_effect=[failure_response, success_response]
            )

            # Should retry and eventually succeed
            events = await fetcher.fetch_calendar(sample_calendar_source)
            assert events == []
            assert mock_client.get.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetcher_context_manager(self):
        """Test CalendarFetcher as async context manager."""
        async with CalendarFetcher() as fetcher:
            assert fetcher._client is not None

        # Client should be closed after context
        assert fetcher._client.is_closed

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_multiple_calendars(self, fetcher):
        """Test fetching multiple calendars concurrently."""
        sources = [
            CalendarSource(
                name=f"Calendar {i}",
                url=f"https://example.com/cal{i}.ics",
                color="#FF0000",
                enabled=True,
                auth=AuthConfig(type=AuthType.NONE),
            )
            for i in range(3)
        ]

        with patch.object(fetcher, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"
            mock_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=mock_response)

            results = await fetcher.fetch_multiple_calendars(sources)

            assert len(results) == 3
            assert mock_client.get.call_count == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, fetcher, sample_calendar_source):
        """Test circuit breaker for failed requests."""
        with patch.object(fetcher, "_client") as mock_client:
            # Simulate multiple failures to trigger circuit breaker
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=mock_response
            )

            mock_client.get = AsyncMock(return_value=mock_response)

            # After multiple failures, circuit breaker should open
            for _ in range(5):
                with pytest.raises(CalendarFetchError):
                    await fetcher.fetch_calendar(sample_calendar_source)

            # Circuit breaker should prevent further requests
            with pytest.raises(CalendarFetchError) as exc_info:
                await fetcher.fetch_calendar(sample_calendar_source)

            assert "Circuit breaker is open" in str(exc_info.value)
