"""RFC 5545 compliant iCal feed generation using icalendar library."""

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
import zoneinfo

from icalendar import Calendar, Event, Timezone, TimezoneStandard, TimezoneDaylight, vDDDTypes
from icalendar.prop import vText

from ..core.logging import get_logger
from ..models.event import EventModel

logger = get_logger(__name__)


class ICalGenerator:
    """RFC 5545 compliant iCal calendar generator."""
    
    def __init__(
        self,
        calendar_name: str = "RallyCal Aggregated Calendar",
        description: str | None = None,
        timezone_name: str = "UTC",
    ) -> None:
        """Initialize the iCal generator.
        
        Args:
            calendar_name: Name of the generated calendar
            description: Description of the calendar
            timezone_name: Default timezone for events
        """
        self.calendar_name = calendar_name
        self.description = description or "Aggregated sports calendar from multiple sources"
        self.timezone_name = timezone_name
        self._generated_at: datetime | None = None
        self._etag: str | None = None
        
        logger.debug(
            "ICalGenerator initialized",
            calendar_name=calendar_name,
            timezone=timezone_name,
        )
    
    def generate_calendar(
        self,
        events: list[EventModel],
        include_timezone: bool = True,
        prodid: str | None = None,
    ) -> str:
        """Generate RFC 5545 compliant iCal feed.
        
        Args:
            events: List of events to include in calendar
            include_timezone: Whether to include VTIMEZONE component
            prodid: Product identifier (defaults to RallyCal)
            
        Returns:
            iCal formatted string
        """
        logger.debug(
            "Generating iCal calendar",
            event_count=len(events),
            include_timezone=include_timezone,
        )
        
        # Create calendar
        cal = Calendar()
        
        # Set calendar properties
        cal.add("prodid", prodid or "-//RallyCal//RallyCal v1.0//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", self.calendar_name)
        cal.add("x-wr-caldesc", self.description)
        cal.add("x-wr-timezone", self.timezone_name)
        
        # Add refresh interval (1 hour)
        cal.add("refresh-interval", "PT1H")
        cal.add("x-published-ttl", "PT1H")
        
        # Add timezone if requested
        if include_timezone and events:
            self._add_timezone_component(cal)
        
        # Add events
        for event in events:
            self._add_event_to_calendar(cal, event)
        
        # Generate calendar content
        calendar_content = cal.to_ical().decode("utf-8")
        
        # Update generation metadata
        self._generated_at = datetime.now(timezone.utc)
        self._etag = self._generate_etag(calendar_content)
        
        logger.info(
            "iCal calendar generated",
            event_count=len(events),
            size_bytes=len(calendar_content),
            etag=self._etag,
        )
        
        return calendar_content
    
    def _add_timezone_component(self, cal: Calendar) -> None:
        """Add VTIMEZONE components for all timezones used by events.
        
        Args:
            cal: Calendar to add timezones to
        """
        # Collect all unique timezones from events
        timezones_needed = set()
        
        # Check all components in calendar for timezone usage
        for component in cal.walk():
            if component.name == "VEVENT":
                # Check DTSTART timezone
                dtstart = component.get("dtstart")
                if dtstart and hasattr(dtstart.dt, "tzinfo") and dtstart.dt.tzinfo:
                    if hasattr(dtstart.dt.tzinfo, "zone"):
                        timezones_needed.add(dtstart.dt.tzinfo.zone)
                    elif hasattr(dtstart.dt.tzinfo, "tzname"):
                        tz_name = dtstart.dt.tzinfo.tzname(dtstart.dt)
                        if tz_name and tz_name != "UTC":
                            timezones_needed.add(tz_name)
                
                # Check DTEND timezone
                dtend = component.get("dtend")
                if dtend and hasattr(dtend.dt, "tzinfo") and dtend.dt.tzinfo:
                    if hasattr(dtend.dt.tzinfo, "zone"):
                        timezones_needed.add(dtend.dt.tzinfo.zone)
                    elif hasattr(dtend.dt.tzinfo, "tzname"):
                        tz_name = dtend.dt.tzinfo.tzname(dtend.dt)
                        if tz_name and tz_name != "UTC":
                            timezones_needed.add(tz_name)
        
        # Add default timezone if specified
        if self.timezone_name and self.timezone_name != "UTC":
            timezones_needed.add(self.timezone_name)
        
        # Generate VTIMEZONE components for each timezone
        for tz_name in timezones_needed:
            try:
                tz_component = self._create_timezone_component(tz_name)
                if tz_component:
                    cal.add_component(tz_component)
                    logger.debug(f"Added timezone component: {tz_name}")
            except Exception as e:
                logger.warning(f"Failed to create timezone component for {tz_name}: {e}")
    
    def _create_timezone_component(self, tz_name: str) -> Timezone | None:
        """Create a VTIMEZONE component for a specific timezone.
        
        Args:
            tz_name: Name of the timezone (e.g., 'America/New_York')
            
        Returns:
            VTIMEZONE component or None if timezone not found
        """
        try:
            # Get timezone info
            try:
                tz_info = zoneinfo.ZoneInfo(tz_name)
            except zoneinfo.ZoneInfoNotFoundError:
                logger.warning(f"Timezone not found: {tz_name}")
                return None
            
            # Create timezone component
            tz = Timezone()
            tz.add("tzid", tz_name)
            
            # Get current year for DST calculations
            current_year = datetime.now().year
            
            # Check for DST transitions in current and next year
            dst_transitions = self._get_dst_transitions(tz_info, current_year)
            
            if not dst_transitions:
                # No DST transitions, create standard time only
                standard = TimezoneStandard()
                
                # Use January 1st as reference
                jan_first = datetime(current_year, 1, 1).replace(tzinfo=tz_info)
                offset = jan_first.utcoffset()
                
                standard.add("dtstart", datetime(1970, 1, 1))
                standard.add("tzoffsetfrom", self._format_offset(offset))
                standard.add("tzoffsetto", self._format_offset(offset))
                standard.add("tzname", jan_first.strftime("%Z"))
                
                tz.add_component(standard)
            else:
                # Has DST transitions, create both standard and daylight components
                for transition in dst_transitions:
                    if transition["is_dst"]:
                        # Daylight time
                        daylight = TimezoneDaylight()
                        daylight.add("dtstart", transition["start"])
                        daylight.add("tzoffsetfrom", self._format_offset(transition["offset_from"]))
                        daylight.add("tzoffsetto", self._format_offset(transition["offset_to"]))
                        daylight.add("tzname", transition["name"])
                        
                        # Add recurrence rule for annual repetition
                        daylight.add("rrule", {"freq": "yearly"})
                        
                        tz.add_component(daylight)
                    else:
                        # Standard time
                        standard = TimezoneStandard()
                        standard.add("dtstart", transition["start"])
                        standard.add("tzoffsetfrom", self._format_offset(transition["offset_from"]))
                        standard.add("tzoffsetto", self._format_offset(transition["offset_to"]))
                        standard.add("tzname", transition["name"])
                        
                        # Add recurrence rule for annual repetition
                        standard.add("rrule", {"freq": "yearly"})
                        
                        tz.add_component(standard)
            
            return tz
            
        except Exception as e:
            logger.error(f"Error creating timezone component for {tz_name}: {e}")
            return None
    
    def _get_dst_transitions(self, tz_info: zoneinfo.ZoneInfo, year: int) -> list[dict[str, Any]]:
        """Get DST transitions for a timezone in a given year.
        
        Args:
            tz_info: ZoneInfo object for the timezone
            year: Year to check for transitions
            
        Returns:
            List of transition dictionaries
        """
        transitions = []
        
        try:
            # Check each month for potential transitions
            for month in range(1, 13):
                for day in [1, 8, 15, 22]:
                    try:
                        dt = datetime(year, month, day, 2, 0).replace(tzinfo=tz_info)
                        
                        # Check if this is a transition point
                        prev_dt = dt.replace(day=day-1) if day > 1 else dt.replace(month=month-1, day=28) if month > 1 else dt.replace(year=year-1, month=12, day=31)
                        prev_dt = prev_dt.replace(tzinfo=tz_info)
                        
                        if dt.dst() != prev_dt.dst():
                            # Found a transition
                            transition = {
                                "start": dt.replace(tzinfo=None),
                                "is_dst": bool(dt.dst()),
                                "offset_from": prev_dt.utcoffset(),
                                "offset_to": dt.utcoffset(),
                                "name": dt.strftime("%Z"),
                            }
                            transitions.append(transition)
                    except (ValueError, OverflowError):
                        # Skip invalid dates
                        continue
        except Exception as e:
            logger.warning(f"Error detecting DST transitions: {e}")
        
        return transitions
    
    def _format_offset(self, offset) -> str:
        """Format timezone offset for iCal.
        
        Args:
            offset: timedelta offset object
            
        Returns:
            Formatted offset string (e.g., "+0500", "-0800")
        """
        if offset is None:
            return "+0000"
        
        total_seconds = int(offset.total_seconds())
        hours, remainder = divmod(abs(total_seconds), 3600)
        minutes = remainder // 60
        
        sign = "+" if total_seconds >= 0 else "-"
        return f"{sign}{hours:02d}{minutes:02d}"
    
    def _add_event_to_calendar(self, cal: Calendar, event: EventModel) -> None:
        """Add an event to the calendar.
        
        Args:
            cal: Calendar to add event to
            event: Event to add
        """
        ical_event = Event()
        
        # Required properties
        ical_event.add("uid", self._generate_event_uid(event))
        ical_event.add("dtstart", event.start_time)
        ical_event.add("dtend", event.end_time)
        ical_event.add("dtstamp", datetime.now(timezone.utc))
        ical_event.add("summary", event.title)
        
        # Optional properties
        if event.description:
            ical_event.add("description", event.description)
        
        if event.location:
            ical_event.add("location", event.location)
        
        # Source identification
        if event.source_name:
            ical_event.add("x-rallycal-source", event.source_name)
        
        # Color coding via categories and custom properties
        if event.color:
            # Standard CATEGORIES property
            category = f"Color-{event.color.lstrip('#').upper()}"
            ical_event.add("categories", [category])
            
            # Custom color property for better client support
            ical_event.add("x-apple-structured-location", event.color)
            ical_event.add("x-microsoft-cdo-busystatus", "BUSY")
            
            # Outlook color support
            color_map = self._get_outlook_color_mapping(event.color)
            if color_map:
                ical_event.add("x-microsoft-cdo-importance", color_map)
        
        # Event categorization
        categories = []
        
        if event.event_type:
            categories.append(event.event_type.title())
        
        if event.tags:
            categories.extend(event.tags)
        
        if categories:
            ical_event.add("categories", categories)
        
        # Source labeling in title if configured
        if event.source_name and not event.title.startswith(f"[{event.source_name}]"):
            enhanced_title = f"[{event.source_name}] {event.title}"
            ical_event["summary"] = enhanced_title
        
        # Metadata preservation
        if hasattr(event, "original_uid") and event.original_uid:
            ical_event.add("x-rallycal-original-uid", event.original_uid)
        
        if hasattr(event, "source_url") and event.source_url:
            ical_event.add("x-rallycal-source-url", event.source_url)
        
        # Last modified timestamp
        if hasattr(event, "last_modified") and event.last_modified:
            ical_event.add("last-modified", event.last_modified)
        else:
            ical_event.add("last-modified", datetime.now(timezone.utc))
        
        # Sequence number for updates
        ical_event.add("sequence", getattr(event, "sequence", 0))
        
        # Status
        ical_event.add("status", "CONFIRMED")
        
        # Transparency (for calendar apps to show as busy/free)
        ical_event.add("transp", "OPAQUE")
        
        cal.add_component(ical_event)
        
        logger.debug(
            "Added event to calendar",
            event_uid=ical_event["uid"],
            event_title=event.title,
            source=event.source_name,
        )
    
    def _generate_event_uid(self, event: EventModel) -> str:
        """Generate a unique identifier for an event.
        
        Args:
            event: Event to generate UID for
            
        Returns:
            Unique event identifier
        """
        # Use original UID if available, otherwise generate one
        if hasattr(event, "original_uid") and event.original_uid:
            return f"{event.original_uid}@rallycal"
        
        # Generate UID based on event content for consistency
        uid_content = f"{event.title}{event.start_time}{event.end_time}{event.source_name}"
        uid_hash = hashlib.md5(uid_content.encode()).hexdigest()
        return f"{uid_hash}@rallycal"
    
    def _get_outlook_color_mapping(self, color: str) -> str | None:
        """Map hex colors to Outlook color categories.
        
        Args:
            color: Hex color string
            
        Returns:
            Outlook color mapping or None
        """
        # Basic color mapping for Outlook compatibility
        color_mappings = {
            "#FF0000": "1",  # Red
            "#00FF00": "2",  # Green
            "#0000FF": "3",  # Blue
            "#FFFF00": "4",  # Yellow
            "#FF00FF": "5",  # Magenta
            "#00FFFF": "6",  # Cyan
            "#FFA500": "7",  # Orange
            "#800080": "8",  # Purple
            "#FFC0CB": "9",  # Pink
            "#A52A2A": "10", # Brown
        }
        
        return color_mappings.get(color.upper())
    
    def _generate_etag(self, content: str) -> str:
        """Generate ETag for caching.
        
        Args:
            content: Calendar content
            
        Returns:
            ETag string
        """
        return f'"{hashlib.md5(content.encode()).hexdigest()}"'
    
    @property
    def etag(self) -> str | None:
        """Get the ETag of the last generated calendar."""
        return self._etag
    
    @property
    def generated_at(self) -> datetime | None:
        """Get the timestamp when calendar was last generated."""
        return self._generated_at
    
    def validate_calendar(self, calendar_content: str) -> tuple[bool, list[str]]:
        """Validate generated calendar for RFC 5545 compliance.
        
        Args:
            calendar_content: iCal content to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Parse the calendar to check for basic validity
            cal = Calendar.from_ical(calendar_content)
            
        except Exception as e:
            errors.append(f"Failed to parse calendar: {e}")
            return False, errors
        
        # RFC 5545 Section 3.4 - Calendar Properties
        # Required VCALENDAR properties
        required_cal_props = {
            "PRODID": "Product identifier is required",
            "VERSION": "Version is required (must be 2.0)"
        }
        
        cal_component = None
        for component in cal.walk():
            if component.name == "VCALENDAR":
                cal_component = component
                break
        
        if not cal_component:
            errors.append("No VCALENDAR component found")
            return False, errors
        
        # Check required calendar properties
        for prop, error_msg in required_cal_props.items():
            if prop not in cal_component:
                errors.append(error_msg)
        
        # Validate VERSION is 2.0
        if "VERSION" in cal_component:
            version = str(cal_component["VERSION"])
            if version != "2.0":
                errors.append(f"VERSION must be 2.0, found: {version}")
        
        # Validate PRODID format
        if "PRODID" in cal_component:
            prodid = str(cal_component["PRODID"])
            if not prodid.startswith("-//") or "//" not in prodid[3:]:
                errors.append(f"PRODID format invalid: {prodid}")
        
        # Check CALSCALE (optional, but if present must be GREGORIAN)
        if "CALSCALE" in cal_component:
            calscale = str(cal_component["CALSCALE"])
            if calscale != "GREGORIAN":
                errors.append(f"CALSCALE must be GREGORIAN if present, found: {calscale}")
        
        # Validate events
        event_errors = self._validate_events(cal)
        errors.extend(event_errors)
        
        # Validate timezone components  
        tz_errors = self._validate_timezones(cal)
        errors.extend(tz_errors)
        
        # Check overall structure
        structure_errors = self._validate_structure(calendar_content)
        errors.extend(structure_errors)
        
        # Check line length (RFC 5545 Section 3.1)
        line_errors = self._validate_line_lengths(calendar_content)
        errors.extend(line_errors)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.debug("Calendar validation passed")
        else:
            logger.warning(f"Calendar validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"Validation error: {error}")
        
        return is_valid, errors
    
    def _validate_events(self, cal: Calendar) -> list[str]:
        """Validate individual events for RFC 5545 compliance.
        
        Args:
            cal: Parsed calendar object
            
        Returns:
            List of validation errors
        """
        errors = []
        event_count = 0
        
        for component in cal.walk():
            if component.name == "VEVENT":
                event_count += 1
                
                # Required properties for VEVENT (RFC 5545 Section 3.6.1)
                required_event_props = {
                    "UID": "Unique identifier is required",
                    "DTSTAMP": "Date-time stamp is required",
                }
                
                for prop, error_msg in required_event_props.items():
                    if prop not in component:
                        errors.append(f"Event {event_count}: {error_msg}")
                
                # Either DTSTART or DTSTART+DTEND or DTSTART+DURATION required
                has_dtstart = "DTSTART" in component
                has_dtend = "DTEND" in component  
                has_duration = "DURATION" in component
                
                if not has_dtstart:
                    errors.append(f"Event {event_count}: DTSTART is required")
                
                if has_dtstart and not (has_dtend or has_duration):
                    errors.append(f"Event {event_count}: Must have either DTEND or DURATION with DTSTART")
                
                if has_dtend and has_duration:
                    errors.append(f"Event {event_count}: Cannot have both DTEND and DURATION")
                
                # Validate UID format
                if "UID" in component:
                    uid = str(component["UID"])
                    if not uid or "@" not in uid:
                        errors.append(f"Event {event_count}: UID should contain '@' for uniqueness")
                
                # Validate SUMMARY length (recommended < 255 chars)
                if "SUMMARY" in component:
                    summary = str(component["SUMMARY"])
                    if len(summary) > 255:
                        errors.append(f"Event {event_count}: SUMMARY longer than 255 characters")
                
                # Validate SEQUENCE is non-negative integer
                if "SEQUENCE" in component:
                    try:
                        sequence = int(component["SEQUENCE"])
                        if sequence < 0:
                            errors.append(f"Event {event_count}: SEQUENCE must be non-negative")
                    except (ValueError, TypeError):
                        errors.append(f"Event {event_count}: SEQUENCE must be integer")
                
                # Validate STATUS values
                if "STATUS" in component:
                    status = str(component["STATUS"])
                    valid_statuses = {"TENTATIVE", "CONFIRMED", "CANCELLED"}
                    if status not in valid_statuses:
                        errors.append(f"Event {event_count}: Invalid STATUS '{status}'")
                
                # Validate TRANSP values
                if "TRANSP" in component:
                    transp = str(component["TRANSP"])
                    valid_transp = {"OPAQUE", "TRANSPARENT"}
                    if transp not in valid_transp:
                        errors.append(f"Event {event_count}: Invalid TRANSP '{transp}'")
        
        if event_count == 0:
            errors.append("No events found in calendar")
        
        return errors
    
    def _validate_timezones(self, cal: Calendar) -> list[str]:
        """Validate timezone components for RFC 5545 compliance.
        
        Args:
            cal: Parsed calendar object
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for component in cal.walk():
            if component.name == "VTIMEZONE":
                # Required properties for VTIMEZONE
                if "TZID" not in component:
                    errors.append("VTIMEZONE: TZID is required")
                
                # Must have at least one STANDARD or DAYLIGHT component
                has_standard = False
                has_daylight = False
                
                for sub_component in component.subcomponents:
                    if sub_component.name == "STANDARD":
                        has_standard = True
                        # Validate STANDARD component
                        std_errors = self._validate_timezone_component(sub_component, "STANDARD")
                        errors.extend(std_errors)
                    elif sub_component.name == "DAYLIGHT":
                        has_daylight = True
                        # Validate DAYLIGHT component  
                        dst_errors = self._validate_timezone_component(sub_component, "DAYLIGHT")
                        errors.extend(dst_errors)
                
                if not (has_standard or has_daylight):
                    errors.append("VTIMEZONE: Must have at least one STANDARD or DAYLIGHT component")
        
        return errors
    
    def _validate_timezone_component(self, component: Any, comp_type: str) -> list[str]:
        """Validate STANDARD or DAYLIGHT timezone component.
        
        Args:
            component: Timezone component to validate
            comp_type: "STANDARD" or "DAYLIGHT"
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required properties for timezone components
        required_props = {
            "DTSTART": "DTSTART is required",
            "TZOFFSETFROM": "TZOFFSETFROM is required",
            "TZOFFSETTO": "TZOFFSETTO is required"
        }
        
        for prop, error_msg in required_props.items():
            if prop not in component:
                errors.append(f"{comp_type}: {error_msg}")
        
        # Validate offset formats
        for offset_prop in ["TZOFFSETFROM", "TZOFFSETTO"]:
            if offset_prop in component:
                offset_value = str(component[offset_prop])
                if not self._validate_offset_format(offset_value):
                    errors.append(f"{comp_type}: Invalid {offset_prop} format: {offset_value}")
        
        return errors
    
    def _validate_offset_format(self, offset: str) -> bool:
        """Validate timezone offset format (+/-HHMM).
        
        Args:
            offset: Offset string to validate
            
        Returns:
            True if valid format
        """
        import re
        pattern = r'^[+-]\d{4}$'
        return bool(re.match(pattern, offset))
    
    def _validate_structure(self, calendar_content: str) -> list[str]:
        """Validate overall calendar structure.
        
        Args:
            calendar_content: Raw calendar content
            
        Returns:
            List of validation errors
        """
        errors = []
        lines = calendar_content.split('\n')
        
        # Must start with BEGIN:VCALENDAR
        if not lines[0].strip().startswith("BEGIN:VCALENDAR"):
            errors.append("Calendar must start with BEGIN:VCALENDAR")
        
        # Must end with END:VCALENDAR
        if not lines[-1].strip().endswith("END:VCALENDAR"):
            errors.append("Calendar must end with END:VCALENDAR")
        
        # Check for balanced BEGIN/END pairs
        begin_stack = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("BEGIN:"):
                component_type = line[6:]
                begin_stack.append((component_type, i + 1))
            elif line.startswith("END:"):
                component_type = line[4:]
                if not begin_stack:
                    errors.append(f"Line {i + 1}: END:{component_type} without matching BEGIN")
                else:
                    begin_type, begin_line = begin_stack.pop()
                    if begin_type != component_type:
                        errors.append(f"Line {i + 1}: END:{component_type} doesn't match BEGIN:{begin_type} on line {begin_line}")
        
        if begin_stack:
            for component_type, line_num in begin_stack:
                errors.append(f"Line {line_num}: BEGIN:{component_type} without matching END")
        
        return errors
    
    def _validate_line_lengths(self, calendar_content: str) -> list[str]:
        """Validate line lengths according to RFC 5545.
        
        Args:
            calendar_content: Raw calendar content
            
        Returns:
            List of validation errors
        """
        errors = []
        lines = calendar_content.split('\n')
        
        for i, line in enumerate(lines):
            # RFC 5545 Section 3.1: Lines should not exceed 75 octets
            if len(line.encode('utf-8')) > 75:
                errors.append(f"Line {i + 1}: Exceeds 75 octets ({len(line.encode('utf-8'))} octets)")
        
        return errors
    
    def generate_http_headers(self) -> dict[str, str]:
        """Generate appropriate HTTP headers for calendar feed.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "text/calendar; charset=utf-8",
            "Cache-Control": "public, max-age=3600",  # 1 hour cache
            "X-Content-Type-Options": "nosniff",
        }
        
        if self._etag:
            headers["ETag"] = self._etag
        
        if self._generated_at:
            headers["Last-Modified"] = self._generated_at.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        
        return headers