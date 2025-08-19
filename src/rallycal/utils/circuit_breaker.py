"""Circuit breaker pattern for graceful degradation of failing services."""

import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, TypeVar

from ..core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, requests blocked  
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for handling failing services."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
        name: str | None = None,
    ) -> None:
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            expected_exception: Exception type that counts as failure
            name: Name for logging purposes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "unnamed"
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.last_success_time: datetime | None = None
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = 0
        
        logger.info(
            "Circuit breaker initialized",
            name=self.name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function raises expected exception
        """
        self.total_requests += 1
        
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                logger.debug(
                    "Circuit breaker open, blocking request",
                    name=self.name,
                    failure_count=self.failure_count,
                )
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if needed
            self._on_success()
            return result
            
        except self.expected_exception as e:
            # Expected failure - increment count and possibly open circuit
            self._on_failure()
            raise e
        
        except Exception as e:
            # Unexpected exception - don't count as circuit failure
            logger.warning(
                "Unexpected exception in circuit breaker",
                name=self.name,
                exception=str(e),
            )
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset.
        
        Returns:
            True if should attempt reset
        """
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now(timezone.utc) - self.last_failure_time
        return time_since_failure >= timedelta(seconds=self.recovery_timeout)
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.state_changes += 1
        logger.info(
            "Circuit breaker transitioning to half-open",
            name=self.name,
        )
    
    def _on_success(self) -> None:
        """Handle successful function execution."""
        self.total_successes += 1
        self.last_success_time = datetime.now(timezone.utc)
        
        if self.state == CircuitState.HALF_OPEN:
            # Success in half-open state - close circuit
            self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed function execution."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        logger.warning(
            "Circuit breaker recorded failure",
            name=self.name,
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state - reopen circuit
            self._open_circuit()
        elif (self.state == CircuitState.CLOSED and 
              self.failure_count >= self.failure_threshold):
            # Too many failures - open circuit
            self._open_circuit()
    
    def _close_circuit(self) -> None:
        """Close the circuit (normal operation)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.state_changes += 1
        
        logger.info(
            "Circuit breaker closed (normal operation)",
            name=self.name,
        )
    
    def _open_circuit(self) -> None:
        """Open the circuit (block requests)."""
        self.state = CircuitState.OPEN
        self.state_changes += 1
        
        logger.error(
            "Circuit breaker opened (blocking requests)",
            name=self.name,
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
        )
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self.state == CircuitState.HALF_OPEN
    
    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "success_rate": (
                self.total_successes / self.total_requests 
                if self.total_requests > 0 else 0.0
            ),
            "state_changes": self.state_changes,
            "last_failure_time": (
                self.last_failure_time.isoformat() 
                if self.last_failure_time else None
            ),
            "last_success_time": (
                self.last_success_time.isoformat() 
                if self.last_success_time else None
            ),
        }
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.state_changes += 1
        
        logger.info(
            "Circuit breaker manually reset",
            name=self.name,
        )


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self) -> None:
        """Initialize circuit breaker registry."""
        self._breakers: dict[str, CircuitBreaker] = {}
        logger.debug("Circuit breaker registry initialized")
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one.
        
        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            expected_exception: Exception type that counts as failure
            
        Returns:
            Circuit breaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                name=name,
            )
            logger.debug(f"Created new circuit breaker: {name}")
        
        return self._breakers[name]
    
    def get(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            Circuit breaker or None if not found
        """
        return self._breakers.get(name)
    
    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers.
        
        Returns:
            Dictionary mapping names to statistics
        """
        return {
            name: breaker.get_stats() 
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("Reset all circuit breakers")
    
    def cleanup_inactive(self, max_age_hours: int = 24) -> int:
        """Clean up circuit breakers that haven't been used recently.
        
        Args:
            max_age_hours: Maximum age in hours for inactive breakers
            
        Returns:
            Number of breakers removed
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        inactive_names = []
        
        for name, breaker in self._breakers.items():
            # Consider breaker inactive if no recent activity
            last_activity = breaker.last_success_time or breaker.last_failure_time
            if not last_activity or last_activity < cutoff_time:
                inactive_names.append(name)
        
        for name in inactive_names:
            del self._breakers[name]
        
        if inactive_names:
            logger.info(
                f"Cleaned up {len(inactive_names)} inactive circuit breakers",
                removed_names=inactive_names,
            )
        
        return len(inactive_names)


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()


def circuit_breaker(
    name: str | None = None,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type[Exception] = Exception,
):
    """Decorator for adding circuit breaker protection to functions.
    
    Args:
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying half-open
        expected_exception: Exception type that counts as failure
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs) -> T:
            breaker = circuit_breaker_registry.get_or_create(
                breaker_name,
                failure_threshold,
                recovery_timeout,
                expected_exception,
            )
            return await breaker.call(func, *args, **kwargs)
        
        def sync_wrapper(*args, **kwargs) -> T:
            breaker = circuit_breaker_registry.get_or_create(
                breaker_name,
                failure_threshold,
                recovery_timeout,
                expected_exception,
            )
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator