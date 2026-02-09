"""
Resilience utilities: retry with backoff and circuit breaker.

Provides decorators and helpers for fault-tolerant Gremlin operations.
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1


class CircuitBreaker:
    """
    Circuit breaker preventing cascading failures.

    States:
        CLOSED  — requests flow normally, failures counted
        OPEN    — requests rejected immediately for `recovery_timeout` seconds
        HALF_OPEN — limited requests allowed to probe recovery
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None, name: str = "default"):
        self._config = config or CircuitBreakerConfig()
        self._name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and (
                    time.monotonic() - self._last_failure_time >= self._config.recovery_timeout
                ):
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker '%s' -> HALF_OPEN", self._name)
            return self._state

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                logger.info("Circuit breaker '%s' -> CLOSED", self._name)
            self._failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker '%s' -> OPEN (failures=%d)",
                    self._name,
                    self._failure_count,
                )

    def allow_request(self) -> bool:
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self._config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
            return False
        return False

    def reset(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
) -> Callable:
    """
    Decorator: retry with exponential backoff and optional circuit breaker.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap.
        exponential_base: Multiplier for exponential backoff.
        retryable_exceptions: Exception types that trigger a retry.
        circuit_breaker: Optional CircuitBreaker instance.

    Example::

        breaker = CircuitBreaker(name="gremlin")

        @retry_with_backoff(max_retries=3, circuit_breaker=breaker)
        def query_graph():
            return g.V().count().next()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if circuit_breaker and not circuit_breaker.allow_request():
                raise CircuitOpenError(
                    f"Circuit breaker '{circuit_breaker._name}' is OPEN — request rejected"
                )

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                except retryable_exceptions as e:
                    last_exception = e
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            delay,
                            e,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries,
                            func.__name__,
                            e,
                        )

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
