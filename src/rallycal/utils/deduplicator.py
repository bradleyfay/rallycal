"""Event deduplication algorithms using fuzzy matching."""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any
from difflib import SequenceMatcher

from ..core.logging import get_logger
from ..models.event import EventModel

logger = get_logger(__name__)


class DuplicationResult:
    """Result of deduplication analysis."""
    
    def __init__(
        self,
        is_duplicate: bool,
        confidence: float,
        canonical_event: EventModel | None = None,
        similarity_factors: dict[str, float] | None = None,
    ) -> None:
        """Initialize duplication result.
        
        Args:
            is_duplicate: Whether event is a duplicate
            confidence: Confidence score (0.0 to 1.0)
            canonical_event: The canonical event if this is a duplicate
            similarity_factors: Breakdown of similarity scores
        """
        self.is_duplicate = is_duplicate
        self.confidence = confidence
        self.canonical_event = canonical_event
        self.similarity_factors = similarity_factors or {}


class EventDeduplicator:
    """Sophisticated event deduplication using multiple matching algorithms."""
    
    def __init__(
        self,
        title_weight: float = 0.4,
        time_weight: float = 0.3,
        location_weight: float = 0.2,
        description_weight: float = 0.1,
        duplicate_threshold: float = 0.8,
        time_tolerance_minutes: int = 30,
    ) -> None:
        """Initialize the deduplicator.
        
        Args:
            title_weight: Weight for title similarity (0.0-1.0)
            time_weight: Weight for time similarity (0.0-1.0)
            location_weight: Weight for location similarity (0.0-1.0)
            description_weight: Weight for description similarity (0.0-1.0)
            duplicate_threshold: Threshold for considering events duplicates (0.0-1.0)
            time_tolerance_minutes: Time difference tolerance in minutes
        """
        self.title_weight = title_weight
        self.time_weight = time_weight
        self.location_weight = location_weight
        self.description_weight = description_weight
        self.duplicate_threshold = duplicate_threshold
        self.time_tolerance = timedelta(minutes=time_tolerance_minutes)
        
        # Validate weights sum to 1.0
        total_weight = title_weight + time_weight + location_weight + description_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, not 1.0. Normalizing...")
            self.title_weight /= total_weight
            self.time_weight /= total_weight
            self.location_weight /= total_weight
            self.description_weight /= total_weight
        
        logger.info(
            "EventDeduplicator initialized",
            duplicate_threshold=duplicate_threshold,
            time_tolerance_minutes=time_tolerance_minutes,
            weights={
                "title": self.title_weight,
                "time": self.time_weight,
                "location": self.location_weight,
                "description": self.description_weight,
            },
        )
    
    def find_duplicates(
        self,
        events: list[EventModel],
        existing_events: list[EventModel] | None = None,
    ) -> dict[str, DuplicationResult]:
        """Find duplicates among events and against existing events.
        
        Args:
            events: New events to check for duplicates
            existing_events: Existing events to check against
            
        Returns:
            Dictionary mapping event IDs to duplication results
        """
        logger.debug(
            "Finding duplicates",
            new_events=len(events),
            existing_events=len(existing_events) if existing_events else 0,
        )
        
        results = {}
        all_events = (existing_events or []) + events
        
        # Create lookup maps for efficient searching
        time_buckets = self._create_time_buckets(all_events)
        
        for event in events:
            # Find potential duplicates in nearby time buckets
            potential_duplicates = self._find_potential_duplicates(
                event,
                time_buckets,
                existing_events or [],
            )
            
            best_match = None
            best_confidence = 0.0
            best_factors = {}
            
            for candidate in potential_duplicates:
                if candidate.id == event.id:
                    continue
                
                similarity_factors = self._calculate_similarity_factors(event, candidate)
                confidence = self._calculate_overall_confidence(similarity_factors)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = candidate
                    best_factors = similarity_factors
            
            # Determine if this is a duplicate
            is_duplicate = best_confidence >= self.duplicate_threshold
            
            results[str(event.id)] = DuplicationResult(
                is_duplicate=is_duplicate,
                confidence=best_confidence,
                canonical_event=best_match if is_duplicate else None,
                similarity_factors=best_factors,
            )
            
            if is_duplicate:
                logger.debug(
                    "Duplicate found",
                    event_id=str(event.id),
                    event_title=event.title,
                    duplicate_of=str(best_match.id),
                    confidence=best_confidence,
                )
        
        duplicate_count = sum(1 for result in results.values() if result.is_duplicate)
        logger.info(
            "Duplicate detection completed",
            total_events=len(events),
            duplicates_found=duplicate_count,
        )
        
        return results
    
    def _create_time_buckets(
        self,
        events: list[EventModel],
        bucket_size_hours: int = 24,
    ) -> dict[str, list[EventModel]]:
        """Create time-based buckets for efficient duplicate searching.
        
        Args:
            events: Events to bucket
            bucket_size_hours: Size of each time bucket in hours
            
        Returns:
            Dictionary mapping bucket keys to events
        """
        buckets = {}
        
        for event in events:
            # Create bucket key based on date (rounded to bucket size)
            bucket_timestamp = event.start_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            bucket_key = bucket_timestamp.isoformat()
            
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(event)
        
        return buckets
    
    def _find_potential_duplicates(
        self,
        event: EventModel,
        time_buckets: dict[str, list[EventModel]],
        existing_events: list[EventModel],
    ) -> list[EventModel]:
        """Find potential duplicate events within time tolerance.
        
        Args:
            event: Event to find duplicates for
            time_buckets: Time-bucketed events
            existing_events: Existing events to prioritize
            
        Returns:
            List of potential duplicate events
        """
        potential_duplicates = []
        
        # Get the bucket for this event's date
        event_date = event.start_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Check current day and adjacent days
        for day_offset in [-1, 0, 1]:
            check_date = event_date + timedelta(days=day_offset)
            bucket_key = check_date.isoformat()
            
            if bucket_key in time_buckets:
                for candidate in time_buckets[bucket_key]:
                    # Check if within time tolerance
                    time_diff = abs(candidate.start_time - event.start_time)
                    if time_diff <= self.time_tolerance:
                        potential_duplicates.append(candidate)
        
        # Prioritize existing events over new events
        potential_duplicates.sort(
            key=lambda e: (
                str(e.id) not in [str(ex.id) for ex in existing_events],
                e.start_time,
            )
        )
        
        return potential_duplicates
    
    def _calculate_similarity_factors(
        self,
        event1: EventModel,
        event2: EventModel,
    ) -> dict[str, float]:
        """Calculate similarity factors between two events.
        
        Args:
            event1: First event
            event2: Second event
            
        Returns:
            Dictionary of similarity factors
        """
        factors = {}
        
        # Title similarity
        factors["title"] = self._calculate_text_similarity(
            event1.title,
            event2.title,
        )
        
        # Time similarity
        factors["time"] = self._calculate_time_similarity(
            event1.start_time,
            event1.end_time,
            event2.start_time,
            event2.end_time,
        )
        
        # Location similarity
        factors["location"] = self._calculate_text_similarity(
            event1.location or "",
            event2.location or "",
        )
        
        # Description similarity
        factors["description"] = self._calculate_text_similarity(
            event1.description or "",
            event2.description or "",
        )
        
        # Additional factors
        factors["source_difference"] = 0.0 if event1.source_name == event2.source_name else 1.0
        factors["event_type_match"] = 1.0 if event1.event_type == event2.event_type else 0.0
        
        return factors
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 and not text2:
            return 1.0
        
        if not text1 or not text2:
            return 0.0
        
        # Normalize text
        norm_text1 = self._normalize_text(text1)
        norm_text2 = self._normalize_text(text2)
        
        if norm_text1 == norm_text2:
            return 1.0
        
        # Use sequence matcher for fuzzy matching
        matcher = SequenceMatcher(None, norm_text1, norm_text2)
        base_similarity = matcher.ratio()
        
        # Boost similarity for common sports event patterns
        boosted_similarity = self._apply_sports_specific_matching(
            text1, text2, base_similarity
        )
        
        return min(1.0, boosted_similarity)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common punctuation
        text = re.sub(r'[.,!?;:()\"\'`]', '', text)
        
        # Normalize common variations
        replacements = {
            ' vs ': ' v ',
            ' versus ': ' v ',
            ' @ ': ' at ',
            ' - ': ' ',
            ' – ': ' ',  # en dash
            ' — ': ' ',  # em dash
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _apply_sports_specific_matching(
        self,
        text1: str,
        text2: str,
        base_similarity: float,
    ) -> float:
        """Apply sports-specific matching rules.
        
        Args:
            text1: First text
            text2: Second text
            base_similarity: Base similarity score
            
        Returns:
            Adjusted similarity score
        """
        # Extract team names and locations
        teams1 = self._extract_team_names(text1)
        teams2 = self._extract_team_names(text2)
        
        # If same teams are involved, boost similarity
        if teams1 and teams2:
            team_overlap = len(teams1.intersection(teams2))
            team_union = len(teams1.union(teams2))
            
            if team_union > 0:
                team_similarity = team_overlap / team_union
                # Boost base similarity by team similarity
                base_similarity = min(1.0, base_similarity + (team_similarity * 0.2))
        
        # Check for game patterns (vs, at, @)
        game_patterns = [r'\bvs?\b', r'\bat\b', r'@']
        has_game_pattern1 = any(re.search(pattern, text1.lower()) for pattern in game_patterns)
        has_game_pattern2 = any(re.search(pattern, text2.lower()) for pattern in game_patterns)
        
        if has_game_pattern1 and has_game_pattern2:
            base_similarity += 0.1
        
        return min(1.0, base_similarity)
    
    def _extract_team_names(self, text: str) -> set[str]:
        """Extract team names from event text.
        
        Args:
            text: Event text
            
        Returns:
            Set of team names
        """
        # Simple extraction based on common patterns
        team_names = set()
        
        # Pattern: "Team A vs Team B"
        vs_match = re.search(r'(.+?)\s+(?:vs?|versus|@|at)\s+(.+)', text, re.IGNORECASE)
        if vs_match:
            team1 = vs_match.group(1).strip()
            team2 = vs_match.group(2).strip()
            
            # Clean up team names
            team1 = re.sub(r'^.*?(eagles|tigers|lions|bears|wolves|sharks|hawks|falcons|panthers|bulls|rams|saints|giants|jets|raiders|chiefs|broncos|steelers|cowboys|patriots|dolphins|bills|cardinals|vikings|packers|49ers|seahawks|chargers|browns|ravens|bengals|titans|jaguars|colts|texans|redskins).*?$', r'\1', team1, flags=re.IGNORECASE)
            team2 = re.sub(r'^.*?(eagles|tigers|lions|bears|wolves|sharks|hawks|falcons|panthers|bulls|rams|saints|giants|jets|raiders|chiefs|broncos|steelers|cowboys|patriots|dolphins|bills|cardinals|vikings|packers|49ers|seahawks|chargers|browns|ravens|bengals|titans|jaguars|colts|texans|redskins).*?$', r'\1', team2, flags=re.IGNORECASE)
            
            if team1:
                team_names.add(team1.lower())
            if team2:
                team_names.add(team2.lower())
        
        return team_names
    
    def _calculate_time_similarity(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime,
    ) -> float:
        """Calculate time similarity between two events.
        
        Args:
            start1: First event start time
            end1: First event end time
            start2: Second event start time
            end2: Second event end time
            
        Returns:
            Time similarity score (0.0 to 1.0)
        """
        # Calculate start time difference
        start_diff = abs(start1 - start2)
        
        # Calculate duration difference
        duration1 = end1 - start1
        duration2 = end2 - start2
        duration_diff = abs(duration1 - duration2)
        
        # Normalize differences to similarity scores
        max_time_diff = self.time_tolerance
        start_similarity = max(0.0, 1.0 - (start_diff.total_seconds() / max_time_diff.total_seconds()))
        
        # Duration similarity (less strict)
        max_duration_diff = timedelta(hours=2)
        duration_similarity = max(0.0, 1.0 - (duration_diff.total_seconds() / max_duration_diff.total_seconds()))
        
        # Weight start time more heavily than duration
        time_similarity = (start_similarity * 0.8) + (duration_similarity * 0.2)
        
        return min(1.0, time_similarity)
    
    def _calculate_overall_confidence(self, factors: dict[str, float]) -> float:
        """Calculate overall confidence score from similarity factors.
        
        Args:
            factors: Dictionary of similarity factors
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        # Base weighted score
        confidence = (
            factors.get("title", 0.0) * self.title_weight +
            factors.get("time", 0.0) * self.time_weight +
            factors.get("location", 0.0) * self.location_weight +
            factors.get("description", 0.0) * self.description_weight
        )
        
        # Apply bonuses/penalties
        if factors.get("source_difference", 0.0) == 0.0:
            # Same source penalty (likely not duplicate if from same source)
            confidence *= 0.7
        
        if factors.get("event_type_match", 0.0) == 1.0:
            # Same event type bonus
            confidence *= 1.1
        
        return min(1.0, confidence)
    
    def merge_duplicate_events(
        self,
        canonical_event: EventModel,
        duplicate_event: EventModel,
    ) -> EventModel:
        """Merge information from duplicate event into canonical event.
        
        Args:
            canonical_event: The canonical event to keep
            duplicate_event: The duplicate event to merge
            
        Returns:
            Updated canonical event with merged information
        """
        logger.debug(
            "Merging duplicate events",
            canonical_id=str(canonical_event.id),
            duplicate_id=str(duplicate_event.id),
        )
        
        # Create a copy to avoid modifying the original
        merged_event = canonical_event.copy()
        
        # Merge descriptions
        if duplicate_event.description and not canonical_event.description:
            merged_event.description = duplicate_event.description
        elif duplicate_event.description and canonical_event.description:
            if duplicate_event.description not in canonical_event.description:
                merged_event.description = f"{canonical_event.description}\n\n{duplicate_event.description}"
        
        # Merge locations (prefer more specific location)
        if duplicate_event.location and not canonical_event.location:
            merged_event.location = duplicate_event.location
        elif (duplicate_event.location and canonical_event.location and 
              len(duplicate_event.location) > len(canonical_event.location)):
            merged_event.location = duplicate_event.location
        
        # Merge tags
        merged_tags = set(canonical_event.tags + duplicate_event.tags)
        merged_event.tags = list(merged_tags)
        
        # Use most recent information
        if duplicate_event.last_modified > canonical_event.last_modified:
            merged_event.last_modified = duplicate_event.last_modified
        
        # Add metadata about the merge
        merged_event.metadata = merged_event.metadata.copy()
        merged_event.metadata["merged_from"] = str(duplicate_event.id)
        merged_event.metadata["merge_timestamp"] = datetime.now().isoformat()
        
        # Mark duplicate event
        duplicate_event.duplicate_of = canonical_event.id
        
        return merged_event