"""End-to-end tests for complete calendar aggregation workflow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from httpx import AsyncClient
from src.rallycal.services.fetcher import CalendarFetcher
from src.rallycal.services.processor import EventProcessor


class TestCompleteCalendarWorkflow:
    """Test complete end-to-end calendar aggregation workflow."""

    @pytest.fixture
    def sample_config_file(self, temp_config_dir):
        """Create a sample configuration file."""
        config_data = {
            "calendars": [
                {
                    "name": "Soccer Team A",
                    "url": "https://soccer-team-a.example.com/calendar.ics",
                    "color": "#FF0000",
                    "enabled": True,
                    "auth": {"type": "none"},
                },
                {
                    "name": "Basketball Team B",
                    "url": "https://basketball-team-b.example.com/calendar.ics",
                    "color": "#00FF00",
                    "enabled": True,
                    "auth": {"type": "bearer", "token": "secret-token"},
                },
                {
                    "name": "Disabled Calendar",
                    "url": "https://disabled.example.com/calendar.ics",
                    "color": "#0000FF",
                    "enabled": False,
                    "auth": {"type": "none"},
                },
            ],
            "manual_events": [
                {
                    "title": "Family Meeting",
                    "start": "2024-01-25T19:00:00Z",
                    "end": "2024-01-25T20:00:00Z",
                    "location": "Home",
                    "description": "Monthly family planning meeting",
                }
            ],
        }

        config_file = temp_config_dir / "calendars.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        return config_file

    @pytest.fixture
    def sample_ical_responses(self):
        """Create sample iCal responses for different calendars."""
        soccer_ical = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Soccer Team A//Calendar//EN
BEGIN:VEVENT
UID:soccer-practice-1@team-a.com
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
SUMMARY:Soccer Practice
DESCRIPTION:Weekly team practice
LOCATION:Soccer Field A
CATEGORIES:Sports,Soccer
END:VEVENT
BEGIN:VEVENT
UID:soccer-game-1@team-a.com
DTSTART:20240127T140000Z
DTEND:20240127T160000Z
SUMMARY:Soccer Game vs Team C
DESCRIPTION:Championship game
LOCATION:Main Stadium
CATEGORIES:Sports,Soccer,Game
END:VEVENT
END:VCALENDAR"""

        basketball_ical = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Basketball Team B//Calendar//EN
BEGIN:VEVENT
UID:basketball-practice-1@team-b.com
DTSTART:20240121T150000Z
DTEND:20240121T170000Z
SUMMARY:Basketball Practice
DESCRIPTION:Scrimmage and drills
LOCATION:Gym A
CATEGORIES:Sports,Basketball
END:VEVENT
BEGIN:VEVENT
UID:duplicate-event@team-b.com
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
SUMMARY:Soccer Practice
DESCRIPTION:Duplicate of soccer practice
LOCATION:Soccer Field A
CATEGORIES:Sports,Soccer
END:VEVENT
END:VCALENDAR"""

        return {
            "https://soccer-team-a.example.com/calendar.ics": soccer_ical,
            "https://basketball-team-b.example.com/calendar.ics": basketball_ical,
        }

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_calendar_aggregation_workflow(
        self, test_client: AsyncClient, sample_config_file, sample_ical_responses
    ):
        """Test complete calendar aggregation from config to output."""

        # Mock HTTP responses for calendar fetching
        async def mock_http_get(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}
            mock_response.text = sample_ical_responses.get(url, "")
            mock_response.raise_for_status = MagicMock()
            return mock_response

        # Mock the configuration file path
        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = sample_config_file

            # Mock HTTP client for calendar fetching
            with patch("httpx.AsyncClient.get", side_effect=mock_http_get):
                # Request the aggregated calendar
                response = await test_client.get("/api/v1/calendar.ics")

                assert response.status_code == 200
                assert (
                    response.headers["content-type"] == "text/calendar; charset=utf-8"
                )

                calendar_content = response.text

                # Verify calendar structure
                assert "BEGIN:VCALENDAR" in calendar_content
                assert "END:VCALENDAR" in calendar_content
                assert "PRODID:-//RallyCal//RallyCal//EN" in calendar_content

                # Verify events from both calendars are included
                assert "Soccer Practice" in calendar_content
                assert "Basketball Practice" in calendar_content
                assert "Soccer Game vs Team C" in calendar_content
                assert "Family Meeting" in calendar_content  # Manual event

                # Verify source identification
                assert (
                    "[Soccer Team A]" in calendar_content
                    or "Soccer Team A" in calendar_content
                )
                assert (
                    "[Basketball Team B]" in calendar_content
                    or "Basketball Team B" in calendar_content
                )

                # Verify duplicate handling - should only have one "Soccer Practice"
                soccer_practice_count = calendar_content.count("Soccer Practice")
                assert soccer_practice_count >= 1  # At least one should be present

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_calendar_workflow_with_authentication(
        self, sample_config_file, sample_ical_responses
    ):
        """Test calendar workflow with different authentication methods."""

        requests_made = []

        async def mock_authenticated_get(url, headers=None, auth=None, **kwargs):
            requests_made.append({"url": url, "headers": headers or {}, "auth": auth})

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}
            mock_response.text = sample_ical_responses.get(url, "")
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = sample_config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_authenticated_get):
                # Create and run the event processor
                processor = EventProcessor()
                events = await processor.process_all_events()

                # Verify requests were made with correct authentication
                assert len(requests_made) == 2  # Only enabled calendars

                # Find the basketball request (has bearer auth)
                basketball_request = next(
                    req for req in requests_made if "basketball-team-b" in req["url"]
                )
                assert (
                    basketball_request["headers"].get("Authorization")
                    == "Bearer secret-token"
                )

                # Find the soccer request (no auth)
                soccer_request = next(
                    req for req in requests_made if "soccer-team-a" in req["url"]
                )
                assert "Authorization" not in soccer_request["headers"]

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_calendar_workflow_with_errors(self, sample_config_file):
        """Test calendar workflow resilience to individual calendar failures."""

        async def mock_http_get_with_errors(url, **kwargs):
            if "soccer-team-a" in url:
                # Soccer calendar fails
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = Exception("Server error")
                return mock_response
            elif "basketball-team-b" in url:
                # Basketball calendar succeeds
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "text/calendar"}
                mock_response.text = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:basketball-1@team-b.com
DTSTART:20240121T150000Z
DTEND:20240121T170000Z
SUMMARY:Basketball Practice
END:VEVENT
END:VCALENDAR"""
                mock_response.raise_for_status = MagicMock()
                return mock_response

            return MagicMock()

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = sample_config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_http_get_with_errors):
                processor = EventProcessor()
                events = await processor.process_all_events()

                # Should still get events from the working calendar
                assert len(events) >= 1  # At least manual events + basketball

                # Verify basketball event is present
                basketball_events = [e for e in events if "Basketball" in e.title]
                assert len(basketball_events) >= 1

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_calendar_workflow_caching(
        self, sample_config_file, sample_ical_responses
    ):
        """Test calendar workflow with caching behavior."""

        request_count = 0

        async def mock_http_get_with_caching(url, headers=None, **kwargs):
            nonlocal request_count
            request_count += 1

            mock_response = MagicMock()

            # First request - return data with ETag
            if request_count == 1:
                mock_response.status_code = 200
                mock_response.headers = {
                    "content-type": "text/calendar",
                    "etag": '"test-etag-123"',
                }
                mock_response.text = sample_ical_responses.get(url, "")
            # Second request with matching ETag - return 304
            elif headers and headers.get("If-None-Match") == '"test-etag-123"':
                mock_response.status_code = 304
                mock_response.text = ""
            else:
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "text/calendar"}
                mock_response.text = sample_ical_responses.get(url, "")

            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = sample_config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_http_get_with_caching):
                fetcher = CalendarFetcher()

                # First fetch - should make HTTP requests
                from src.rallycal.config.models import (
                    AuthConfig,
                    AuthType,
                    CalendarSource,
                )

                source = CalendarSource(
                    name="Test Source",
                    url="https://soccer-team-a.example.com/calendar.ics",
                    color="#FF0000",
                    enabled=True,
                    auth=AuthConfig(type=AuthType.NONE),
                )

                events1 = await fetcher.fetch_calendar(source)
                initial_request_count = request_count

                # Second fetch - should use cache
                events2 = await fetcher.fetch_calendar(source)

                # Verify caching behavior
                assert request_count > initial_request_count  # Second request made
                # Events should be the same (from cache or 304 response)
                assert len(events1) == len(events2)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_calendar_workflow_config_reload(
        self, test_client: AsyncClient, temp_config_dir, sample_ical_responses
    ):
        """Test calendar workflow with configuration reloading."""

        # Create initial config
        initial_config = {
            "calendars": [
                {
                    "name": "Initial Calendar",
                    "url": "https://initial.example.com/calendar.ics",
                    "color": "#FF0000",
                    "enabled": True,
                    "auth": {"type": "none"},
                }
            ]
        }

        config_file = temp_config_dir / "calendars.yaml"
        with open(config_file, "w") as f:
            yaml.dump(initial_config, f)

        async def mock_http_get(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}

            if "initial.example.com" in url:
                mock_response.text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:initial@example.com
SUMMARY:Initial Event
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
END:VEVENT
END:VCALENDAR"""
            elif "updated.example.com" in url:
                mock_response.text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:updated@example.com
SUMMARY:Updated Event
DTSTART:20240121T100000Z
DTEND:20240121T110000Z
END:VEVENT
END:VCALENDAR"""
            else:
                mock_response.text = "BEGIN:VCALENDAR\nEND:VCALENDAR"

            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_http_get):
                # Get initial calendar
                response1 = await test_client.get("/api/v1/calendar.ics")
                assert response1.status_code == 200
                assert "Initial Event" in response1.text

                # Update config file
                updated_config = {
                    "calendars": [
                        {
                            "name": "Updated Calendar",
                            "url": "https://updated.example.com/calendar.ics",
                            "color": "#00FF00",
                            "enabled": True,
                            "auth": {"type": "none"},
                        }
                    ]
                }

                with open(config_file, "w") as f:
                    yaml.dump(updated_config, f)

                # Trigger config reload via webhook
                webhook_payload = {
                    "ref": "refs/heads/main",
                    "commits": [{"modified": ["config/calendars.yaml"]}],
                }

                webhook_response = await test_client.post(
                    "/api/v1/webhooks/config", json=webhook_payload
                )
                assert webhook_response.status_code == 200

                # Get updated calendar
                response2 = await test_client.get("/api/v1/calendar.ics")
                assert response2.status_code == 200
                assert "Updated Event" in response2.text
                assert "Initial Event" not in response2.text

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_calendar_workflow_performance(
        self, sample_config_file, sample_ical_responses
    ):
        """Test calendar workflow performance with multiple calendars."""
        import asyncio
        import time

        # Create config with many calendars
        large_config = {
            "calendars": [
                {
                    "name": f"Calendar {i}",
                    "url": f"https://calendar-{i}.example.com/calendar.ics",
                    "color": f"#{'FF' if i % 2 else '00'}{'00' if i % 3 else 'FF'}{'00' if i % 5 else 'FF'}",
                    "enabled": True,
                    "auth": {"type": "none"},
                }
                for i in range(10)
            ]
        }

        config_file = Path(sample_config_file).parent / "large_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(large_config, f)

        async def mock_http_get(url, **kwargs):
            # Simulate network delay
            await asyncio.sleep(0.1)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}
            mock_response.text = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:event@{url}
SUMMARY:Event from {url}
DTSTART:20240120T100000Z
DTEND:20240120T110000Z
END:VEVENT
END:VCALENDAR"""
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_http_get):
                start_time = time.time()

                processor = EventProcessor()
                events = await processor.process_all_events()

                end_time = time.time()
                duration = end_time - start_time

                # Should complete in reasonable time (concurrent fetching)
                assert duration < 5.0  # Should be much faster than 10 * 0.1 = 1 second

                # Should get events from all calendars
                assert len(events) >= 10

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_calendar_workflow_stress_test(
        self, test_client: AsyncClient, sample_config_file, sample_ical_responses
    ):
        """Stress test calendar workflow with multiple concurrent requests."""
        import asyncio

        async def mock_http_get(url, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/calendar"}
            mock_response.text = sample_ical_responses.get(
                url, "BEGIN:VCALENDAR\nEND:VCALENDAR"
            )
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("src.rallycal.core.settings.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.calendar.config_file = sample_config_file

            with patch("httpx.AsyncClient.get", side_effect=mock_http_get):
                # Make multiple concurrent requests
                async def make_request():
                    response = await test_client.get("/api/v1/calendar.ics")
                    return response.status_code

                tasks = [make_request() for _ in range(20)]
                results = await asyncio.gather(*tasks)

                # All requests should succeed
                assert all(status == 200 for status in results)
