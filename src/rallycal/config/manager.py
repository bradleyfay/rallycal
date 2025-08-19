"""Configuration file management with YAML parsing and validation."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..core.logging import get_logger
from .models import CalendarConfig, CalendarSource, ManualEvent

logger = get_logger(__name__)


class ConfigChangeHandler(FileSystemEventHandler):
    """Handle configuration file changes."""

    def __init__(self, config_manager: "ConfigManager") -> None:
        """Initialize the change handler.

        Args:
            config_manager: ConfigManager instance to notify of changes
        """
        super().__init__()
        self.config_manager = config_manager
        self.debounce_timer: asyncio.Handle | None = None
        self.debounce_delay = 1.0  # 1 second debounce

    def on_modified(self, event) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path == self.config_manager.config_file:
            logger.debug(f"Configuration file modified: {file_path}")
            self._debounced_reload()

    def _debounced_reload(self) -> None:
        """Debounced configuration reload to handle rapid file changes."""
        if self.debounce_timer:
            self.debounce_timer.cancel()

        loop = asyncio.get_event_loop()
        self.debounce_timer = loop.call_later(
            self.debounce_delay,
            lambda: asyncio.create_task(self.config_manager._reload_config()),
        )


class ConfigManager:
    """Manages calendar configuration with file watching and validation."""

    def __init__(
        self,
        config_file: Path | str,
        auto_reload: bool = True,
        change_callback: Callable[[CalendarConfig], None] | None = None,
    ) -> None:
        """Initialize the configuration manager.

        Args:
            config_file: Path to the configuration YAML file
            auto_reload: Whether to automatically reload on file changes
            change_callback: Optional callback for configuration changes
        """
        self.config_file = Path(config_file)
        self.auto_reload = auto_reload
        self.change_callback = change_callback

        self._config: CalendarConfig | None = None
        self._last_loaded: datetime | None = None
        self._observer: Observer | None = None
        self._change_handler: ConfigChangeHandler | None = None

        logger.info(
            "ConfigManager initialized",
            config_file=str(self.config_file),
            auto_reload=auto_reload,
        )

    async def load_config(self) -> CalendarConfig:
        """Load and validate configuration from file.

        Returns:
            Validated calendar configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
            yaml.YAMLError: If YAML parsing fails
        """
        logger.debug(f"Loading configuration from {self.config_file}")

        if not self.config_file.exists():
            msg = f"Configuration file not found: {self.config_file}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            # Read YAML file
            with open(self.config_file, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)

            if raw_config is None:
                raw_config = {}

            # Validate configuration
            config = CalendarConfig(**raw_config)

            # Store configuration and metadata
            self._config = config
            self._last_loaded = datetime.now(UTC)

            # Start file watching if enabled
            if self.auto_reload and not self._observer:
                self._start_file_watching()

            logger.info(
                "Configuration loaded successfully",
                calendar_count=len(config.calendars),
                manual_event_count=len(config.manual_events),
            )

            return config

        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML configuration: {e}"
            logger.error(msg)
            raise

        except ValidationError as e:
            msg = f"Configuration validation failed: {e}"
            logger.error(msg)
            raise

        except Exception as e:
            msg = f"Unexpected error loading configuration: {e}"
            logger.error(msg)
            raise

    async def save_config(self, config: CalendarConfig) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save

        Raises:
            ValidationError: If config is invalid
            PermissionError: If file cannot be written
        """
        logger.debug(f"Saving configuration to {self.config_file}")

        try:
            # Validate configuration
            config_dict = config.dict(exclude_none=True, by_alias=True)

            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write YAML file with proper formatting
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=False,
                    allow_unicode=True,
                )

            # Update stored configuration
            self._config = config
            self._last_loaded = datetime.now(UTC)

            logger.info("Configuration saved successfully")

        except Exception as e:
            msg = f"Failed to save configuration: {e}"
            logger.error(msg)
            raise

    async def _reload_config(self) -> None:
        """Reload configuration from file (internal method)."""
        try:
            old_config = self._config
            new_config = await self.load_config()

            # Check if configuration actually changed
            if old_config and old_config == new_config:
                logger.debug("Configuration unchanged, skipping reload")
                return

            logger.info("Configuration reloaded due to file change")

            # Notify callback if provided
            if self.change_callback:
                try:
                    self.change_callback(new_config)
                except Exception as e:
                    logger.error(f"Error in configuration change callback: {e}")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    def _start_file_watching(self) -> None:
        """Start watching configuration file for changes."""
        if self._observer:
            return

        self._change_handler = ConfigChangeHandler(self)
        self._observer = Observer()
        self._observer.schedule(
            self._change_handler,
            str(self.config_file.parent),
            recursive=False,
        )
        self._observer.start()

        logger.debug(f"Started watching configuration file: {self.config_file}")

    def stop_watching(self) -> None:
        """Stop watching configuration file for changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._change_handler = None

            logger.debug("Stopped watching configuration file")

    async def get_config(self) -> CalendarConfig:
        """Get current configuration, loading if necessary.

        Returns:
            Current calendar configuration
        """
        if self._config is None:
            await self.load_config()

        return self._config

    async def get_calendar_sources(self) -> list[CalendarSource]:
        """Get enabled calendar sources.

        Returns:
            List of enabled calendar sources
        """
        config = await self.get_config()
        return [cal for cal in config.calendars if cal.enabled]

    async def get_manual_events(self) -> list[ManualEvent]:
        """Get manual events from configuration.

        Returns:
            List of manual events
        """
        config = await self.get_config()
        return config.manual_events

    async def add_calendar_source(self, calendar: CalendarSource) -> None:
        """Add a new calendar source to configuration.

        Args:
            calendar: Calendar source to add

        Raises:
            ValidationError: If calendar configuration is invalid
            ValueError: If calendar name or URL already exists
        """
        config = await self.get_config()

        # Check for duplicate names
        existing_names = {cal.name for cal in config.calendars}
        if calendar.name in existing_names:
            msg = f"Calendar with name '{calendar.name}' already exists"
            raise ValueError(msg)

        # Check for duplicate URLs
        existing_urls = {cal.url for cal in config.calendars}
        if calendar.url in existing_urls:
            msg = f"Calendar with URL '{calendar.url}' already exists"
            raise ValueError(msg)

        # Add calendar and save
        config.calendars.append(calendar)
        await self.save_config(config)

        logger.info(f"Added calendar source: {calendar.name}")

    async def remove_calendar_source(self, name: str) -> bool:
        """Remove a calendar source by name.

        Args:
            name: Name of calendar source to remove

        Returns:
            True if calendar was removed, False if not found
        """
        config = await self.get_config()

        original_count = len(config.calendars)
        config.calendars = [cal for cal in config.calendars if cal.name != name]

        if len(config.calendars) < original_count:
            await self.save_config(config)
            logger.info(f"Removed calendar source: {name}")
            return True

        logger.warning(f"Calendar source not found for removal: {name}")
        return False

    async def update_calendar_source(
        self,
        name: str,
        updates: dict[str, Any],
    ) -> bool:
        """Update a calendar source.

        Args:
            name: Name of calendar source to update
            updates: Dictionary of fields to update

        Returns:
            True if calendar was updated, False if not found
        """
        config = await self.get_config()

        for calendar in config.calendars:
            if calendar.name == name:
                # Update fields
                for field, value in updates.items():
                    if hasattr(calendar, field):
                        setattr(calendar, field, value)

                # Validate updated configuration
                CalendarConfig.validate(config.dict())

                await self.save_config(config)
                logger.info(f"Updated calendar source: {name}")
                return True

        logger.warning(f"Calendar source not found for update: {name}")
        return False

    async def add_manual_event(self, event: ManualEvent) -> None:
        """Add a manual event to configuration.

        Args:
            event: Manual event to add
        """
        config = await self.get_config()
        config.manual_events.append(event)
        await self.save_config(config)

        logger.info(f"Added manual event: {event.title}")

    async def validate_config_file(self) -> tuple[bool, list[str]]:
        """Validate configuration file without loading.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            if not self.config_file.exists():
                errors.append(f"Configuration file not found: {self.config_file}")
                return False, errors

            # Parse YAML
            with open(self.config_file, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)

            # Validate structure
            CalendarConfig(**raw_config or {})

            return True, []

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")

        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                errors.append(f"{field}: {error['msg']}")

        except Exception as e:
            errors.append(f"Unexpected error: {e}")

        return False, errors

    @property
    def is_loaded(self) -> bool:
        """Check if configuration is currently loaded."""
        return self._config is not None

    @property
    def last_loaded(self) -> datetime | None:
        """Get timestamp when configuration was last loaded."""
        return self._last_loaded

    async def create_default_config(self) -> None:
        """Create a default configuration file if none exists."""
        if self.config_file.exists():
            logger.warning("Configuration file already exists, not creating default")
            return

        # Create default configuration
        default_config = CalendarConfig(
            calendars=[
                CalendarSource(
                    name="Example Team Calendar",
                    url="https://example.com/team-calendar.ics",
                    color="#FF0000",
                    enabled=False,  # Disabled by default
                )
            ],
            manual_events=[],
            global_settings={
                "refresh_interval": 3600,
                "max_events_per_calendar": 1000,
                "default_timezone": "UTC",
            },
        )

        await self.save_config(default_config)
        logger.info(f"Created default configuration file: {self.config_file}")

    def __del__(self) -> None:
        """Cleanup when manager is destroyed."""
        if self._observer:
            self.stop_watching()
