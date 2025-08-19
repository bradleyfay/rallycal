"""Async calendar fetching service using httpx with connection pooling."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
from icalendar import Calendar
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config.models import AuthConfig, AuthType, CalendarSource
from ..core.logging import get_logger
from ..models.event import EventModel, EventStatus, EventType

logger = get_logger(__name__)


class CalendarFetchError(Exception):
    """Base exception for calendar fetching errors."""

    pass


class AuthenticationError(CalendarFetchError):
    """Authentication failed."""

    pass


class TimeoutError(CalendarFetchError):
    """Request timed out."""

    pass


class ParsingError(CalendarFetchError):
    """Failed to parse calendar data."""

    pass


class CalendarFetcher:
    """Async calendar fetcher with connection pooling and retry logic."""

    def __init__(
        self,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
        keepalive_expiry: float = 30.0,
        default_timeout: float = 30.0,
    ) -> None:
        """Initialize the calendar fetcher.

        Args:
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum keepalive connections
            keepalive_expiry: Keepalive expiry time in seconds
            default_timeout: Default request timeout in seconds
        """
        self.default_timeout = default_timeout

        # Create connection limits
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry,
        )

        # Create async client with connection pooling
        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(default_timeout),
            follow_redirects=True,
            headers={
                "User-Agent": "RallyCal/1.0 (Sports Calendar Aggregator)",
                "Accept": "text/calendar, application/calendar, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
                "Cache-Control": "no-cache",
            },
        )

        logger.info(
            "CalendarFetcher initialized",
            max_connections=max_connections,
            default_timeout=default_timeout,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and connections."""
        await self._client.aclose()
        logger.debug("CalendarFetcher closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
    )
    async def fetch_calendar(
        self,
        calendar_source: CalendarSource,
        if_modified_since: datetime | None = None,
        if_none_match: str | None = None,
    ) -> tuple[str, dict[str, str]]:
        """Fetch calendar data from a source with caching support.

        Args:
            calendar_source: Calendar source configuration
            if_modified_since: Last modified timestamp for conditional requests
            if_none_match: ETag for conditional requests

        Returns:
            Tuple of (calendar_data, response_headers)

        Raises:
            CalendarFetchError: If fetching fails
            AuthenticationError: If authentication fails
            TimeoutError: If request times out
        """
        logger.debug(
            "Fetching calendar",
            source_name=calendar_source.name,
            url=calendar_source.url,
        )

        # Prepare headers
        headers = self._prepare_headers(
            calendar_source.auth,
            if_modified_since,
            if_none_match,
        )

        # Prepare timeout
        timeout = httpx.Timeout(calendar_source.timeout)

        try:
            response = await self._client.get(
                calendar_source.url,
                headers=headers,
                timeout=timeout,
            )

            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed for {calendar_source.name}"
                )

            # Handle not modified responses
            if response.status_code == 304:
                logger.debug(f"Calendar not modified: {calendar_source.name}")
                return "", dict(response.headers)

            # Handle other errors
            response.raise_for_status()

            # Get calendar data
            calendar_data = response.text

            # Validate it's actually calendar data
            if not self._is_valid_calendar_content(calendar_data):
                raise ParsingError(
                    f"Invalid calendar content from {calendar_source.name}"
                )

            logger.info(
                "Calendar fetched successfully",
                source_name=calendar_source.name,
                size_bytes=len(calendar_data),
                content_type=response.headers.get("content-type"),
            )

            return calendar_data, dict(response.headers)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching calendar {calendar_source.name}: {e}")
            raise TimeoutError(f"Timeout fetching {calendar_source.name}") from e

        except httpx.RequestError as e:
            logger.error(f"Request error fetching calendar {calendar_source.name}: {e}")
            raise CalendarFetchError(
                f"Request failed for {calendar_source.name}"
            ) from e

        except Exception as e:
            logger.error(
                f"Unexpected error fetching calendar {calendar_source.name}: {e}"
            )
            raise CalendarFetchError(
                f"Unexpected error for {calendar_source.name}"
            ) from e

    def _prepare_headers(
        self,
        auth_config: AuthConfig,
        if_modified_since: datetime | None = None,
        if_none_match: str | None = None,
    ) -> dict[str, str]:
        """Prepare HTTP headers including authentication and caching.

        Args:
            auth_config: Authentication configuration
            if_modified_since: Last modified timestamp
            if_none_match: ETag value

        Returns:
            Dictionary of HTTP headers
        """
        headers = {}

        # Add authentication headers
        if auth_config.type == AuthType.BASIC:
            import base64

            credentials = f"{auth_config.username}:{auth_config.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"

        elif auth_config.type == AuthType.BEARER:
            headers["Authorization"] = f"Bearer {auth_config.token}"

        elif auth_config.type == AuthType.API_KEY:
            headers[auth_config.api_key_header] = auth_config.token

        # Add caching headers
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

        if if_none_match:
            headers["If-None-Match"] = if_none_match

        return headers

    def _is_valid_calendar_content(self, content: str) -> bool:
        """Validate that content appears to be calendar data.

        Args:
            content: Raw content to validate

        Returns:
            True if content appears to be calendar data
        """
        if not content.strip():
            return False

        # Check for basic calendar markers
        content_upper = content.upper()
        required_markers = ["BEGIN:VCALENDAR", "END:VCALENDAR"]

        for marker in required_markers:
            if marker not in content_upper:
                return False

        return True

    async def parse_calendar_events(
        self,
        calendar_data: str,
        source_name: str,
        source_url: str,
        source_color: str | None = None,
        max_events: int = 1000,
        filter_keywords: list[str] | None = None,
        exclude_keywords: list[str] | None = None,
    ) -> list[EventModel]:
        """Parse calendar data and extract events.

        Args:
            calendar_data: Raw calendar data
            source_name: Name of the calendar source
            source_url: URL of the calendar source
            source_color: Color for events from this source
            max_events: Maximum number of events to process
            filter_keywords: Keywords to filter events (include only)
            exclude_keywords: Keywords to exclude events

        Returns:
            List of parsed events

        Raises:
            ParsingError: If parsing fails
        """
        logger.debug(
            "Parsing calendar events",
            source_name=source_name,
            max_events=max_events,
        )

        try:
            # Parse calendar with icalendar
            calendar = Calendar.from_ical(calendar_data)

            events = []
            processed_count = 0

            for component in calendar.walk():
                if component.name != "VEVENT":
                    continue

                if processed_count >= max_events:
                    logger.warning(
                        f"Reached max events limit ({max_events}) for {source_name}"
                    )
                    break

                try:
                    event = self._parse_event_component(
                        component,
                        source_name,
                        source_url,
                        source_color,
                    )

                    # Apply filtering
                    if self._should_include_event(
                        event,
                        filter_keywords,
                        exclude_keywords,
                    ):
                        events.append(event)

                    processed_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to parse event in {source_name}: {e}",
                        exc_info=True,
                    )
                    continue

            logger.info(
                "Calendar events parsed",
                source_name=source_name,
                total_events=len(events),
                processed_count=processed_count,
            )

            return events

        except Exception as e:
            logger.error(f"Failed to parse calendar {source_name}: {e}")
            raise ParsingError(f"Failed to parse calendar {source_name}") from e

    def _parse_event_component(
        self,
        component: Any,
        source_name: str,
        source_url: str,
        source_color: str | None,
    ) -> EventModel:
        """Parse a single event component.

        Args:
            component: iCal event component
            source_name: Name of the calendar source
            source_url: URL of the calendar source
            source_color: Color for the event

        Returns:
            Parsed event model
        """
        # Extract basic event data
        title = str(component.get("summary", "Untitled Event"))
        description = (
            str(component.get("description", ""))
            if component.get("description")
            else None
        )
        location = (
            str(component.get("location", "")) if component.get("location") else None
        )

        # Extract dates
        dtstart = component.get("dtstart")
        dtend = component.get("dtend")

        if not dtstart:
            raise ValueError("Event missing DTSTART")

        start_time = dtstart.dt
        if dtend:
            end_time = dtend.dt
        else:
            # Default to 1 hour duration if no end time
            from datetime import timedelta

            end_time = start_time + timedelta(hours=1)

        # Handle timezone-naive dates
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=UTC)

        # Extract optional fields
        uid = str(component.get("uid", "")) if component.get("uid") else None
        status_str = str(component.get("status", "CONFIRMED")).upper()

        # Map status
        status_mapping = {
            "CONFIRMED": EventStatus.CONFIRMED,
            "TENTATIVE": EventStatus.TENTATIVE,
            "CANCELLED": EventStatus.CANCELLED,
        }
        status = status_mapping.get(status_str, EventStatus.CONFIRMED)

        # Extract categories for event type detection
        categories = component.get("categories")
        event_type = self._detect_event_type(title, description, categories)

        # Extract tags from categories
        tags = []
        if categories:
            if isinstance(categories, str):
                tags = [categories.strip()]
            elif hasattr(categories, "cats"):  # icalendar Categories object
                tags = [str(cat).strip() for cat in categories.cats]

        # Create event model
        event = EventModel(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            source_name=source_name,
            source_url=source_url,
            color=source_color,
            event_type=event_type,
            status=status,
            original_uid=uid,
            tags=tags,
            metadata={
                "raw_status": status_str,
                "has_timezone": dtstart.dt.tzinfo is not None,
            },
        )

        # Update content hash for deduplication
        event.update_hash()

        return event

    def _detect_event_type(
        self,
        title: str,
        description: str | None,
        categories: Any,
    ) -> EventType | None:
        """Detect event type from title, description, and categories.

        Args:
            title: Event title
            description: Event description
            categories: Event categories

        Returns:
            Detected event type or None
        """
        # Combine text for analysis
        text_content = title.lower()
        if description:
            text_content += " " + description.lower()

        # Category mapping
        if categories:
            cat_text = str(categories).lower()
            text_content += " " + cat_text

        # Define keywords for each event type
        type_keywords = {
            EventType.GAME: ["game", "match", "competition", "vs", "against", "@"],
            EventType.PRACTICE: [
                "practice",
                "training",
                "drill",
                "scrimmage",
                "workout",
            ],
            EventType.TOURNAMENT: [
                "tournament",
                "championship",
                "cup",
                "classic",
                "invitational",
            ],
            EventType.MEETING: ["meeting", "parent", "team meeting", "coach meeting"],
            EventType.FUNDRAISER: ["fundraiser", "car wash", "bake sale", "raffle"],
            EventType.SOCIAL: ["party", "banquet", "celebration", "picnic", "bbq"],
            EventType.TRAVEL: ["travel", "departure", "bus", "carpool", "transport"],
        }

        # Check for keywords
        for event_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in text_content:
                    return event_type

        return None

    def _should_include_event(
        self,
        event: EventModel,
        filter_keywords: list[str] | None,
        exclude_keywords: list[str] | None,
    ) -> bool:
        """Determine if event should be included based on filtering rules.

        Args:
            event: Event to check
            filter_keywords: Keywords to filter for (include only)
            exclude_keywords: Keywords to exclude

        Returns:
            True if event should be included
        """
        # Combine searchable text
        searchable_text = event.title.lower()
        if event.description:
            searchable_text += " " + event.description.lower()
        if event.location:
            searchable_text += " " + event.location.lower()

        # Check exclude keywords first
        if exclude_keywords:
            for keyword in exclude_keywords:
                if keyword.lower() in searchable_text:
                    return False

        # Check filter keywords
        if filter_keywords:
            for keyword in filter_keywords:
                if keyword.lower() in searchable_text:
                    return True
            # If filter keywords are specified but none match, exclude
            return False

        # Include by default if no filtering rules apply
        return True

    async def fetch_multiple_calendars(
        self,
        calendar_sources: list[CalendarSource],
        concurrency_limit: int = 5,
    ) -> dict[str, tuple[list[EventModel], Exception | None]]:
        """Fetch multiple calendars concurrently.

        Args:
            calendar_sources: List of calendar sources to fetch
            concurrency_limit: Maximum concurrent requests

        Returns:
            Dictionary mapping source names to (events, error) tuples
        """
        logger.info(
            "Fetching multiple calendars",
            source_count=len(calendar_sources),
            concurrency_limit=concurrency_limit,
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def fetch_single_calendar(source: CalendarSource):
            async with semaphore:
                try:
                    calendar_data, headers = await self.fetch_calendar(source)
                    if not calendar_data:  # Not modified
                        return source.name, ([], None)

                    events = await self.parse_calendar_events(
                        calendar_data,
                        source.name,
                        source.url,
                        source.color,
                        source.max_events,
                        source.filter_keywords,
                        source.exclude_keywords,
                    )
                    return source.name, (events, None)

                except Exception as e:
                    logger.error(f"Failed to fetch calendar {source.name}: {e}")
                    return source.name, ([], e)

        # Execute all fetches concurrently
        tasks = [fetch_single_calendar(source) for source in calendar_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        result_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
                continue

            source_name, (events, error) = result
            result_dict[source_name] = (events, error)

        successful_fetches = sum(
            1 for events, error in result_dict.values() if error is None
        )
        logger.info(
            "Multiple calendar fetch completed",
            total_sources=len(calendar_sources),
            successful_fetches=successful_fetches,
        )

        return result_dict
