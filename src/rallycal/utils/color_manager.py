"""Color assignment and management for calendar events and sources."""

import hashlib
import re
from typing import Any

from ..core.logging import get_logger

logger = get_logger(__name__)


class ColorManager:
    """Manages color assignment with consistent hashing and visual optimization."""
    
    # Predefined color palette optimized for calendar visibility
    DEFAULT_PALETTE = [
        "#FF5722",  # Deep Orange
        "#2196F3",  # Blue
        "#4CAF50",  # Green
        "#FF9800",  # Orange
        "#9C27B0",  # Purple
        "#F44336",  # Red
        "#009688",  # Teal
        "#3F51B5",  # Indigo
        "#8BC34A",  # Light Green
        "#FF5722",  # Deep Orange
        "#795548",  # Brown
        "#607D8B",  # Blue Grey
        "#E91E63",  # Pink
        "#CDDC39",  # Lime
        "#FFC107",  # Amber
        "#673AB7",  # Deep Purple
        "#00BCD4",  # Cyan
        "#FFEB3B",  # Yellow
        "#9E9E9E",  # Grey
        "#FF6F00",  # Orange (Dark)
    ]
    
    # Sport-specific color mappings
    SPORT_COLORS = {
        "soccer": "#00AA00",      # Green
        "football": "#8B4513",    # Brown
        "basketball": "#FF8800",  # Orange
        "baseball": "#FF0000",    # Red
        "hockey": "#0066CC",      # Blue
        "tennis": "#FFFF00",      # Yellow
        "swimming": "#00CCFF",    # Cyan
        "track": "#FF6600",       # Orange Red
        "volleyball": "#FF69B4",  # Hot Pink
        "lacrosse": "#800080",    # Purple
        "wrestling": "#8B0000",   # Dark Red
        "golf": "#228B22",        # Forest Green
        "cross country": "#DC143C", # Crimson
        "softball": "#FFD700",    # Gold
    }
    
    # Team name color mappings (consistent colors for common team names)
    TEAM_COLORS = {
        "eagles": "#8B4513",      # Brown
        "tigers": "#FF8C00",      # Dark Orange
        "lions": "#DAA520",       # Goldenrod
        "bears": "#654321",       # Dark Brown
        "wolves": "#696969",      # Dim Gray
        "sharks": "#4682B4",      # Steel Blue
        "hawks": "#8B0000",       # Dark Red
        "falcons": "#2F4F4F",     # Dark Slate Gray
        "panthers": "#000000",    # Black
        "bulls": "#DC143C",       # Crimson
        "rams": "#4169E1",        # Royal Blue
        "saints": "#FFD700",      # Gold
        "giants": "#0000FF",      # Blue
        "jets": "#006400",        # Dark Green
        "raiders": "#C0C0C0",     # Silver
        "chiefs": "#FF0000",      # Red
        "broncos": "#FF8C00",     # Dark Orange
        "steelers": "#000000",    # Black
        "cowboys": "#4169E1",     # Royal Blue
        "patriots": "#002244",    # Navy
        "dolphins": "#008B8B",    # Dark Cyan
        "cardinals": "#8B0000",   # Dark Red
        "vikings": "#4B0082",     # Indigo
        "packers": "#006400",     # Dark Green
        "seahawks": "#005A8B",    # Navy Blue
        "chargers": "#FFD700",    # Gold
        "ravens": "#4B0082",      # Indigo
        "titans": "#4169E1",      # Royal Blue
    }
    
    def __init__(
        self,
        custom_palette: list[str] | None = None,
        use_sport_colors: bool = True,
        use_team_colors: bool = True,
    ) -> None:
        """Initialize the color manager.
        
        Args:
            custom_palette: Custom color palette to use
            use_sport_colors: Whether to use sport-specific colors
            use_team_colors: Whether to use team-specific colors
        """
        self.palette = custom_palette or self.DEFAULT_PALETTE
        self.use_sport_colors = use_sport_colors
        self.use_team_colors = use_team_colors
        
        # Validate palette colors
        self.palette = [self._validate_color(color) for color in self.palette]
        
        logger.info(
            "ColorManager initialized",
            palette_size=len(self.palette),
            use_sport_colors=use_sport_colors,
            use_team_colors=use_team_colors,
        )
    
    def assign_color(
        self,
        identifier: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Assign a color based on identifier with consistent hashing.
        
        Args:
            identifier: Unique identifier (e.g., calendar name, team name)
            context: Additional context for color assignment
            
        Returns:
            Hex color string (#RRGGBB)
        """
        context = context or {}
        
        # Check for sport-specific colors
        if self.use_sport_colors:
            sport_color = self._get_sport_color(identifier, context)
            if sport_color:
                logger.debug(f"Assigned sport color {sport_color} to {identifier}")
                return sport_color
        
        # Check for team-specific colors
        if self.use_team_colors:
            team_color = self._get_team_color(identifier, context)
            if team_color:
                logger.debug(f"Assigned team color {team_color} to {identifier}")
                return team_color
        
        # Use consistent hashing for deterministic color assignment
        hash_color = self._hash_to_color(identifier)
        logger.debug(f"Assigned hash color {hash_color} to {identifier}")
        return hash_color
    
    def _get_sport_color(
        self,
        identifier: str,
        context: dict[str, Any],
    ) -> str | None:
        """Get sport-specific color if applicable.
        
        Args:
            identifier: Identifier to check
            context: Additional context
            
        Returns:
            Sport color or None
        """
        # Check context for explicit sport
        sport = context.get("sport", "").lower()
        if sport in self.SPORT_COLORS:
            return self.SPORT_COLORS[sport]
        
        # Check identifier for sport keywords
        identifier_lower = identifier.lower()
        for sport_name, color in self.SPORT_COLORS.items():
            if sport_name in identifier_lower:
                return color
        
        return None
    
    def _get_team_color(
        self,
        identifier: str,
        context: dict[str, Any],
    ) -> str | None:
        """Get team-specific color if applicable.
        
        Args:
            identifier: Identifier to check
            context: Additional context
            
        Returns:
            Team color or None
        """
        # Check context for explicit team
        team = context.get("team", "").lower()
        if team in self.TEAM_COLORS:
            return self.TEAM_COLORS[team]
        
        # Check identifier for team names
        identifier_lower = identifier.lower()
        for team_name, color in self.TEAM_COLORS.items():
            if team_name in identifier_lower:
                return color
        
        return None
    
    def _hash_to_color(self, identifier: str) -> str:
        """Convert identifier to color using consistent hashing.
        
        Args:
            identifier: String to hash
            
        Returns:
            Hex color from palette
        """
        # Create MD5 hash of identifier
        hash_object = hashlib.md5(identifier.encode())
        hash_bytes = hash_object.digest()
        
        # Convert to integer and map to palette index
        hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        palette_index = hash_int % len(self.palette)
        
        return self.palette[palette_index]
    
    def _validate_color(self, color: str) -> str:
        """Validate and normalize color format.
        
        Args:
            color: Color string to validate
            
        Returns:
            Validated hex color
            
        Raises:
            ValueError: If color format is invalid
        """
        # Remove whitespace
        color = color.strip()
        
        # Add # if missing
        if not color.startswith('#'):
            color = '#' + color
        
        # Validate hex format
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError(f"Invalid color format: {color}")
        
        return color.upper()
    
    def get_contrasting_text_color(self, background_color: str) -> str:
        """Get contrasting text color for a background color.
        
        Args:
            background_color: Background color hex string
            
        Returns:
            Contrasting text color (black or white)
        """
        # Remove # if present
        hex_color = background_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Calculate relative luminance
        # Formula from WCAG 2.0
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return black for light backgrounds, white for dark
        return "#000000" if luminance > 0.5 else "#FFFFFF"
    
    def generate_color_palette(
        self,
        count: int,
        base_color: str | None = None,
        saturation_range: tuple[float, float] = (0.6, 0.9),
        lightness_range: tuple[float, float] = (0.4, 0.7),
    ) -> list[str]:
        """Generate a harmonious color palette.
        
        Args:
            count: Number of colors to generate
            base_color: Base color to build palette from
            saturation_range: Range of saturation values (0.0 to 1.0)
            lightness_range: Range of lightness values (0.0 to 1.0)
            
        Returns:
            List of hex colors
        """
        import colorsys
        
        colors = []
        
        if base_color:
            # Convert base color to HSL
            base_rgb = self._hex_to_rgb(base_color)
            base_hsl = colorsys.rgb_to_hls(*[c/255.0 for c in base_rgb])
            base_hue = base_hsl[0]
        else:
            base_hue = 0.0
        
        # Generate colors with varying hue
        for i in range(count):
            # Calculate hue with even distribution
            hue = (base_hue + (i / count)) % 1.0
            
            # Vary saturation and lightness
            sat_min, sat_max = saturation_range
            light_min, light_max = lightness_range
            
            saturation = sat_min + ((sat_max - sat_min) * (i % 3) / 2)
            lightness = light_min + ((light_max - light_min) * (i % 2))
            
            # Convert back to RGB and hex
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            hex_color = self._rgb_to_hex([int(c * 255) for c in rgb])
            colors.append(hex_color)
        
        return colors
    
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string
            
        Returns:
            RGB tuple
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color.
        
        Args:
            rgb: RGB tuple
            
        Returns:
            Hex color string
        """
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    
    def analyze_color_distribution(self, colors: list[str]) -> dict[str, Any]:
        """Analyze the distribution of colors for optimization.
        
        Args:
            colors: List of colors to analyze
            
        Returns:
            Analysis results
        """
        if not colors:
            return {"total_colors": 0}
        
        # Count unique colors
        unique_colors = set(colors)
        
        # Analyze color properties
        hues = []
        saturations = []
        lightnesses = []
        
        import colorsys
        
        for color in unique_colors:
            rgb = self._hex_to_rgb(color)
            hsl = colorsys.rgb_to_hls(*[c/255.0 for c in rgb])
            hues.append(hsl[0])
            lightnesses.append(hsl[1])
            saturations.append(hsl[2])
        
        return {
            "total_colors": len(colors),
            "unique_colors": len(unique_colors),
            "color_reuse_rate": len(colors) / len(unique_colors) if unique_colors else 0,
            "hue_range": (min(hues), max(hues)) if hues else (0, 0),
            "saturation_range": (min(saturations), max(saturations)) if saturations else (0, 0),
            "lightness_range": (min(lightnesses), max(lightnesses)) if lightnesses else (0, 0),
            "average_saturation": sum(saturations) / len(saturations) if saturations else 0,
            "average_lightness": sum(lightnesses) / len(lightnesses) if lightnesses else 0,
        }
    
    def get_calendar_color_scheme(
        self,
        calendar_sources: list[dict[str, Any]],
    ) -> dict[str, str]:
        """Generate optimal color scheme for calendar sources.
        
        Args:
            calendar_sources: List of calendar source configurations
            
        Returns:
            Dictionary mapping source names to colors
        """
        color_scheme = {}
        
        # Sort sources by priority (sport-specific, team-specific, then hash)
        def source_priority(source):
            name = source.get("name", "").lower()
            priority = 0
            
            # Sport-specific sources get highest priority
            if any(sport in name for sport in self.SPORT_COLORS):
                priority += 100
            
            # Team-specific sources get medium priority
            if any(team in name for team in self.TEAM_COLORS):
                priority += 50
            
            return priority
        
        sorted_sources = sorted(calendar_sources, key=source_priority, reverse=True)
        
        # Assign colors
        used_colors = set()
        
        for source in sorted_sources:
            name = source.get("name", "")
            context = source.get("context", {})
            
            # Try to assign color
            color = self.assign_color(name, context)
            
            # If color is already used, find alternative
            if color in used_colors:
                color = self._find_alternative_color(color, used_colors)
            
            color_scheme[name] = color
            used_colors.add(color)
        
        logger.info(
            "Generated color scheme",
            source_count=len(calendar_sources),
            unique_colors=len(used_colors),
        )
        
        return color_scheme
    
    def _find_alternative_color(
        self,
        preferred_color: str,
        used_colors: set[str],
    ) -> str:
        """Find alternative color when preferred is already used.
        
        Args:
            preferred_color: The preferred color that's already used
            used_colors: Set of already used colors
            
        Returns:
            Alternative color
        """
        # Try generating variants of the preferred color
        import colorsys
        
        rgb = self._hex_to_rgb(preferred_color)
        hsl = colorsys.rgb_to_hls(*[c/255.0 for c in rgb])
        
        # Try different lightness values
        for lightness_offset in [0.1, -0.1, 0.2, -0.2]:
            new_lightness = max(0.2, min(0.8, hsl[1] + lightness_offset))
            new_hsl = (hsl[0], new_lightness, hsl[2])
            new_rgb = colorsys.hls_to_rgb(*new_hsl)
            new_color = self._rgb_to_hex([int(c * 255) for c in new_rgb])
            
            if new_color not in used_colors:
                return new_color
        
        # Fall back to palette colors
        for color in self.palette:
            if color not in used_colors:
                return color
        
        # Last resort: return preferred color anyway
        return preferred_color