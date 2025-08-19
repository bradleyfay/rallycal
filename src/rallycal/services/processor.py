"""Event processing, merging, and title formatting services."""

import re
from typing import Any

from ..core.logging import get_logger
from ..models.event import EventModel, EventStatus, EventType
from ..utils.color_manager import ColorManager
from ..utils.deduplicator import EventDeduplicator

logger = get_logger(__name__)


class TitleFormatter:
    """Configurable event title formatting with source identification."""

    def __init__(
        self,
        include_source_labels: bool = True,
        include_event_type: bool = False,
        max_title_length: int = 100,
        source_label_format: str = "[{source}]",
        type_label_format: str = "({type})",
        separator: str = " ",
    ) -> None:
        """Initialize title formatter.

        Args:
            include_source_labels: Whether to add source labels to titles
            include_event_type: Whether to add event type labels
            max_title_length: Maximum title length (truncate if longer)
            source_label_format: Format string for source labels
            type_label_format: Format string for type labels
            separator: Separator between components
        """
        self.include_source_labels = include_source_labels
        self.include_event_type = include_event_type
        self.max_title_length = max_title_length
        self.source_label_format = source_label_format
        self.type_label_format = type_label_format
        self.separator = separator

        logger.debug(
            "TitleFormatter initialized",
            include_source_labels=include_source_labels,
            include_event_type=include_event_type,
            max_title_length=max_title_length,
        )

    def format_title(
        self,
        event: EventModel,
        custom_format: str | None = None,
    ) -> str:
        """Format event title with configured options.

        Args:
            event: Event to format title for
            custom_format: Optional custom format string

        Returns:
            Formatted title
        """
        if custom_format:
            return self._apply_custom_format(event, custom_format)

        # Start with original title
        components = []

        # Add source label if enabled and not already present
        if (
            self.include_source_labels
            and event.source_name
            and not self._has_source_label(event.title, event.source_name)
        ):
            source_label = self.source_label_format.format(source=event.source_name)
            components.append(source_label)

        # Add original title
        clean_title = self._clean_title(event.title)
        components.append(clean_title)

        # Add event type if enabled
        if (
            self.include_event_type
            and event.event_type
            and not self._has_type_indicator(clean_title)
        ):
            type_label = self.type_label_format.format(
                type=event.event_type.value.title()
            )
            components.append(type_label)

        # Join components
        formatted_title = self.separator.join(components)

        # Truncate if necessary
        if len(formatted_title) > self.max_title_length:
            formatted_title = self._truncate_title(formatted_title)

        return formatted_title

    def _has_source_label(self, title: str, source_name: str) -> bool:
        """Check if title already contains source label.

        Args:
            title: Event title
            source_name: Source name to check for

        Returns:
            True if source label is already present
        """
        # Check for common source label patterns
        patterns = [
            rf"\[{re.escape(source_name)}\]",
            rf"\({re.escape(source_name)}\)",
            rf"{re.escape(source_name)}:",
            rf"^{re.escape(source_name)}\s",
        ]

        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True

        return False

    def _has_type_indicator(self, title: str) -> bool:
        """Check if title already indicates event type.

        Args:
            title: Event title

        Returns:
            True if type indicator is present
        """
        # Common type indicators
        type_indicators = [
            "game",
            "match",
            "vs",
            "v ",
            "@",
            "practice",
            "training",
            "drill",
            "tournament",
            "championship",
            "cup",
            "meeting",
            "scrimmage",
            "workout",
        ]

        title_lower = title.lower()
        return any(indicator in title_lower for indicator in type_indicators)

    def _clean_title(self, title: str) -> str:
        """Clean up title text.

        Args:
            title: Original title

        Returns:
            Cleaned title
        """
        # Remove extra whitespace
        title = re.sub(r"\s+", " ", title).strip()

        # Remove duplicate punctuation
        title = re.sub(r"[.]{2,}", "...", title)
        title = re.sub(r"[!]{2,}", "!", title)
        title = re.sub(r"[?]{2,}", "?", title)

        return title

    def _truncate_title(self, title: str) -> str:
        """Truncate title to maximum length.

        Args:
            title: Title to truncate

        Returns:
            Truncated title
        """
        if len(title) <= self.max_title_length:
            return title

        # Try to truncate at word boundary
        truncated = title[: self.max_title_length - 3]

        # Find last space for word boundary
        last_space = truncated.rfind(" ")
        if last_space > self.max_title_length * 0.7:  # Only if we don't lose too much
            truncated = truncated[:last_space]

        return truncated + "..."

    def _apply_custom_format(self, event: EventModel, format_string: str) -> str:
        """Apply custom format string to event.

        Args:
            event: Event to format
            format_string: Custom format string with placeholders

        Returns:
            Formatted title
        """
        # Available placeholders
        placeholders = {
            "{title}": event.title,
            "{source}": event.source_name or "",
            "{type}": event.event_type.value.title() if event.event_type else "",
            "{location}": event.location or "",
            "{date}": event.start_time.strftime("%m/%d"),
            "{time}": event.start_time.strftime("%H:%M"),
            "{day}": event.start_time.strftime("%a"),
            "{status}": event.status.value.title(),
        }

        # Replace placeholders
        formatted = format_string
        for placeholder, value in placeholders.items():
            formatted = formatted.replace(placeholder, value)

        # Clean up extra spaces
        formatted = re.sub(r"\s+", " ", formatted).strip()

        return formatted


class EventProcessor:
    """Main event processing service for aggregation and formatting."""

    def __init__(
        self,
        deduplicator: EventDeduplicator | None = None,
        title_formatter: TitleFormatter | None = None,
        color_manager: ColorManager | None = None,
    ) -> None:
        """Initialize event processor.

        Args:
            deduplicator: Event deduplicator instance
            title_formatter: Title formatter instance
            color_manager: Color manager instance
        """
        self.deduplicator = deduplicator or EventDeduplicator()
        self.title_formatter = title_formatter or TitleFormatter()
        self.color_manager = color_manager or ColorManager()

        logger.info("EventProcessor initialized")

    async def process_events(
        self,
        new_events: list[EventModel],
        existing_events: list[EventModel] | None = None,
        apply_formatting: bool = True,
        apply_colors: bool = True,
        detect_duplicates: bool = True,
    ) -> dict[str, Any]:
        """Process events with deduplication, formatting, and color assignment.

        Args:
            new_events: New events to process
            existing_events: Existing events for duplicate detection
            apply_formatting: Whether to apply title formatting
            apply_colors: Whether to assign colors
            detect_duplicates: Whether to detect duplicates

        Returns:
            Processing results dictionary
        """
        logger.info(
            "Processing events",
            new_events=len(new_events),
            existing_events=len(existing_events) if existing_events else 0,
        )

        results = {
            "processed_events": [],
            "duplicate_events": [],
            "statistics": {
                "total_input": len(new_events),
                "unique_events": 0,
                "duplicates_found": 0,
                "formatted_titles": 0,
                "colors_assigned": 0,
            },
        }

        # Detect duplicates if enabled
        duplicate_results = {}
        if detect_duplicates and existing_events:
            duplicate_results = self.deduplicator.find_duplicates(
                new_events,
                existing_events,
            )

        # Process each event
        for event in new_events:
            event_id = str(event.id)

            # Check if this event is a duplicate
            is_duplicate = (
                duplicate_results.get(event_id, {}).is_duplicate
                if duplicate_results
                else False
            )

            if is_duplicate:
                duplicate_result = duplicate_results[event_id]
                canonical_event = duplicate_result.canonical_event

                # Merge duplicate into canonical event
                if canonical_event:
                    merged_event = self.deduplicator.merge_duplicate_events(
                        canonical_event,
                        event,
                    )
                    # Update the canonical event in results
                    for i, existing in enumerate(results["processed_events"]):
                        if existing.id == canonical_event.id:
                            results["processed_events"][i] = merged_event
                            break

                results["duplicate_events"].append(event)
                results["statistics"]["duplicates_found"] += 1

                logger.debug(
                    "Event marked as duplicate",
                    event_id=event_id,
                    canonical_id=str(canonical_event.id) if canonical_event else None,
                    confidence=duplicate_result.confidence,
                )
                continue

            # Apply title formatting if enabled
            if apply_formatting:
                original_title = event.title
                event.title = self.title_formatter.format_title(event)

                if event.title != original_title:
                    results["statistics"]["formatted_titles"] += 1
                    logger.debug(
                        "Title formatted",
                        event_id=event_id,
                        original=original_title,
                        formatted=event.title,
                    )

            # Apply color assignment if enabled and no color set
            if apply_colors and not event.color:
                context = {
                    "sport": self._detect_sport_from_event(event),
                    "team": self._extract_team_name(event.title),
                }

                event.color = self.color_manager.assign_color(
                    event.source_name,
                    context,
                )
                results["statistics"]["colors_assigned"] += 1

                logger.debug(
                    "Color assigned",
                    event_id=event_id,
                    color=event.color,
                    source=event.source_name,
                )

            results["processed_events"].append(event)
            results["statistics"]["unique_events"] += 1

        logger.info(
            "Event processing completed",
            unique_events=results["statistics"]["unique_events"],
            duplicates=results["statistics"]["duplicates_found"],
            formatted_titles=results["statistics"]["formatted_titles"],
            colors_assigned=results["statistics"]["colors_assigned"],
        )

        return results

    def _detect_sport_from_event(self, event: EventModel) -> str | None:
        """Detect sport type from event information.

        Args:
            event: Event to analyze

        Returns:
            Detected sport or None
        """
        # Combine searchable text
        text_content = event.title.lower()
        if event.description:
            text_content += " " + event.description.lower()
        if event.location:
            text_content += " " + event.location.lower()

        # Sport keywords
        sport_keywords = {
            "soccer": ["soccer", "futbol", "football"],
            "basketball": ["basketball", "hoops", "bball"],
            "baseball": ["baseball", "ball", "diamond"],
            "hockey": ["hockey", "ice", "puck"],
            "tennis": ["tennis", "court", "racket"],
            "swimming": ["swim", "pool", "stroke"],
            "track": ["track", "field", "run", "sprint"],
            "volleyball": ["volleyball", "vball", "spike"],
            "golf": ["golf", "course", "tee"],
            "wrestling": ["wrestling", "mat", "pin"],
        }

        for sport, keywords in sport_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                return sport

        return None

    def _extract_team_name(self, title: str) -> str | None:
        """Extract team name from title.

        Args:
            title: Event title

        Returns:
            Extracted team name or None
        """
        # Simple team name extraction
        # Look for patterns like "Eagles vs Hawks" or "at Eagles"
        vs_match = re.search(
            r"(\w+)\s+(?:vs?|versus|@|at)\s+(\w+)", title, re.IGNORECASE
        )
        if vs_match:
            # Return the first team mentioned
            return vs_match.group(1).lower()

        # Look for team name patterns
        team_pattern = re.search(
            r"\b(eagles|tigers|lions|bears|wolves|sharks|hawks|falcons|panthers|bulls|rams)\b",
            title,
            re.IGNORECASE,
        )
        if team_pattern:
            return team_pattern.group(1).lower()

        return None

    async def detect_overlapping_events(
        self,
        events: list[EventModel],
        overlap_threshold_minutes: int = 15,
    ) -> list[tuple[EventModel, EventModel]]:
        """Detect overlapping events from different sources.

        Args:
            events: Events to check for overlaps
            overlap_threshold_minutes: Minimum overlap in minutes to flag

        Returns:
            List of overlapping event pairs
        """
        overlaps = []

        # Sort events by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)

        for i, event1 in enumerate(sorted_events):
            for event2 in sorted_events[i + 1 :]:
                # Stop if event2 starts after event1 ends
                if event2.start_time >= event1.end_time:
                    break

                # Skip if same source (not really an overlap issue)
                if event1.source_name == event2.source_name:
                    continue

                # Calculate overlap
                overlap_start = max(event1.start_time, event2.start_time)
                overlap_end = min(event1.end_time, event2.end_time)
                overlap_duration = (overlap_end - overlap_start).total_seconds() / 60

                if overlap_duration >= overlap_threshold_minutes:
                    overlaps.append((event1, event2))

                    logger.debug(
                        "Overlapping events detected",
                        event1_id=str(event1.id),
                        event1_title=event1.title,
                        event2_id=str(event2.id),
                        event2_title=event2.title,
                        overlap_minutes=overlap_duration,
                    )

        logger.info(f"Found {len(overlaps)} overlapping event pairs")
        return overlaps

    async def resolve_overlaps(
        self,
        overlapping_pairs: list[tuple[EventModel, EventModel]],
        resolution_strategy: str = "mark_conflict",
    ) -> list[EventModel]:
        """Resolve overlapping events.

        Args:
            overlapping_pairs: List of overlapping event pairs
            resolution_strategy: How to resolve overlaps

        Returns:
            List of resolved events
        """
        resolved_events = []

        for event1, event2 in overlapping_pairs:
            if resolution_strategy == "mark_conflict":
                # Add conflict markers to titles
                if "CONFLICT" not in event1.title:
                    event1.title = f"⚠️ CONFLICT: {event1.title}"
                if "CONFLICT" not in event2.title:
                    event2.title = f"⚠️ CONFLICT: {event2.title}"

                resolved_events.extend([event1, event2])

            elif resolution_strategy == "merge_overlapping":
                # Create merged event spanning both
                merged_event = EventModel(
                    title=f"Multiple Events: {event1.title} / {event2.title}",
                    start_time=min(event1.start_time, event2.start_time),
                    end_time=max(event1.end_time, event2.end_time),
                    source_name="Multiple Sources",
                    description=f"Overlapping events:\n1. {event1.title}\n2. {event2.title}",
                    color="#FF6600",  # Orange for conflicts
                    event_type=EventType.OTHER,
                    status=EventStatus.TENTATIVE,
                )
                resolved_events.append(merged_event)

            elif resolution_strategy == "prefer_longer":
                # Keep the longer event
                duration1 = (event1.end_time - event1.start_time).total_seconds()
                duration2 = (event2.end_time - event2.start_time).total_seconds()

                preferred_event = event1 if duration1 >= duration2 else event2
                resolved_events.append(preferred_event)

        logger.info(
            f"Resolved {len(overlapping_pairs)} overlapping pairs using {resolution_strategy}"
        )

        return resolved_events
