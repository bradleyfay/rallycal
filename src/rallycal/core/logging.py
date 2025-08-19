"""Structured logging configuration using loguru."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from .settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure structured logging with loguru.
    
    Args:
        settings: Application settings containing logging configuration
    """
    # Remove default loguru handler
    logger.remove()
    
    # Determine log level based on environment
    if settings.is_development:
        log_level = "DEBUG"
        show_time = True
        colorize = True
        backtrace = True
        diagnose = True
    elif settings.environment == "testing":
        log_level = "WARNING"
        show_time = False
        colorize = False
        backtrace = False
        diagnose = False
    else:  # staging/production
        log_level = "INFO"
        show_time = True
        colorize = False
        backtrace = False
        diagnose = False
    
    # Console handler with environment-appropriate formatting
    console_format = _get_console_format(
        show_time=show_time,
        colorize=colorize,
        environment=settings.environment,
    )
    
    logger.add(
        sink=sys.stderr,
        format=console_format,
        level=log_level,
        colorize=colorize,
        backtrace=backtrace,
        diagnose=diagnose,
        enqueue=True,  # Thread-safe logging
        catch=True,    # Catch exceptions in logging
    )
    
    # File handler for non-development environments
    if not settings.is_development:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Application log file
        logger.add(
            sink=log_dir / "rallycal.log",
            format=_get_file_format(),
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            enqueue=True,
            catch=True,
            serialize=False,  # Human-readable format
        )
        
        # Error log file (ERROR and above only)
        logger.add(
            sink=log_dir / "rallycal_errors.log",
            format=_get_file_format(),
            level="ERROR",
            rotation="10 MB", 
            retention="90 days",
            compression="gz",
            enqueue=True,
            catch=True,
            serialize=False,
        )
        
        # JSON structured log for production monitoring
        if settings.is_production:
            logger.add(
                sink=log_dir / "rallycal_structured.jsonl",
                format=_get_json_format(),
                level="INFO",
                rotation="50 MB",
                retention="30 days",
                compression="gz",
                enqueue=True,
                catch=True,
                serialize=True,  # JSON format
            )
    
    # Configure loguru to handle standard library logging
    import logging
    
    class InterceptHandler(logging.Handler):
        """Intercept standard library logs and redirect to loguru."""
        
        def emit(self, record: logging.LogRecord) -> None:
            """Emit log record through loguru."""
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where originated the logged message
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Replace standard library root logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Suppress noisy third-party loggers
    _configure_third_party_loggers()
    
    # Log startup message
    logger.info(
        "Logging configured",
        environment=settings.environment,
        level=log_level,
        debug=settings.debug,
    )


def _get_console_format(show_time: bool, colorize: bool, environment: str) -> str:
    """Get console log format based on environment.
    
    Args:
        show_time: Whether to show timestamp
        colorize: Whether to colorize output
        environment: Application environment
        
    Returns:
        Log format string
    """
    if environment == "development":
        if show_time:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        else:
            return (
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
    else:
        # Production/staging format (no colors, more structured)
        if show_time:
            return (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )
        else:
            return (
                "{level: <8} | "
                "{name}:{function}:{line} | " 
                "{message}"
            )


def _get_file_format() -> str:
    """Get file log format (human-readable).
    
    Returns:
        Log format string for file output
    """
    return (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{process.id} | "
        "{thread.id} | "
        "{name}:{function}:{line} | "
        "{message}"
    )


def _get_json_format() -> str:
    """Get JSON log format for structured logging.
    
    Returns:
        Log format string for JSON output
    """
    return (
        '{{"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
        '"level": "{level}", '
        '"process_id": {process.id}, '
        '"thread_id": {thread.id}, '
        '"module": "{name}", '
        '"function": "{function}", '
        '"line": {line}, '
        '"message": "{message}"}}'
    )


def _configure_third_party_loggers() -> None:
    """Configure third-party library loggers to reduce noise."""
    # Suppress noisy loggers
    noisy_loggers = [
        "urllib3.connectionpool",
        "asyncio",
        "aiosqlite",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Reduce SQLAlchemy INFO logging in non-debug mode
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(component=name)


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """Log function call with parameters.
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger.debug(
        "Function called",
        function=func_name,
        parameters=kwargs,
    )


def log_exception(exc: Exception, context: str | None = None) -> None:
    """Log exception with context.
    
    Args:
        exc: Exception to log
        context: Additional context about where exception occurred
    """
    logger.exception(
        "Exception occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        context=context,
    )


def log_performance(operation: str, duration: float, **metadata: Any) -> None:
    """Log performance metrics.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        **metadata: Additional metadata to log
    """
    logger.info(
        "Performance metric",
        operation=operation,
        duration_seconds=duration,
        **metadata,
    )