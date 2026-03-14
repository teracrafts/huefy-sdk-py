"""Circuit breaker pattern for resilient API calls."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and requests are being rejected."""

    def __init__(self, message: str = "Circuit breaker is open", reset_timeout: float = 0.0) -> None:
        super().__init__(message)
        self.reset_timeout = reset_timeout


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker.

    Attributes:
        failure_threshold: Number of consecutive failures before opening the circuit.
        reset_timeout: Seconds to wait before transitioning from OPEN to HALF_OPEN.
        half_open_requests: Number of requests allowed in HALF_OPEN state.
    """
    failure_threshold: int = 5
    reset_timeout: float = 30.0
    half_open_requests: int = 1


@dataclass
class CircuitBreakerStats:
    """Runtime statistics for the circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None


class CircuitBreaker:
    """Circuit breaker implementation for protecting against cascading failures.

    The circuit breaker transitions between three states:
    - CLOSED: Normal operation. Failures are counted.
    - OPEN: Requests are rejected immediately. Transitions to HALF_OPEN after reset_timeout.
    - HALF_OPEN: A limited number of requests are allowed through. Success closes the circuit;
      failure reopens it.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_requests = 0
        self._half_open_requests = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None
        self._opened_at: float | None = None
        # Lock is created lazily so that the CircuitBreaker can be instantiated
        # outside an async context (e.g. at module level) without binding to a
        # specific event loop.
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        """Return the asyncio.Lock, creating it lazily on first async use."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def execute(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Execute a function through the circuit breaker.

        Args:
            fn: An async callable to execute.

        Returns:
            The result of the callable.

        Raises:
            CircuitOpenError: If the circuit is open and not ready to transition.
        """
        async with self._get_lock():
            self._total_requests += 1

            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                else:
                    raise CircuitOpenError(
                        message="Circuit breaker is open — requests are being rejected",
                        reset_timeout=self._config.reset_timeout,
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_requests >= self._config.half_open_requests:
                    raise CircuitOpenError(
                        message="Circuit breaker is half-open — max probe requests reached",
                        reset_timeout=self._config.reset_timeout,
                    )
                self._half_open_requests += 1

        # fn() runs outside the lock to avoid holding it during I/O
        try:
            result = await fn()
        except Exception:
            async with self._get_lock():
                self._on_failure()
            raise

        async with self._get_lock():
            self._on_success()
        return result

    async def get_state(self) -> CircuitState:
        """Get the current circuit breaker state."""
        async with self._get_lock():
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    async def reset(self) -> None:
        """Reset the circuit breaker to its initial closed state."""
        async with self._get_lock():
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_requests = 0
            self._opened_at = None

    async def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        async with self._get_lock():
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN and self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            return CircuitBreakerStats(
                state=self._state,
                failure_count=self._failure_count,
                success_count=self._success_count,
                total_requests=self._total_requests,
                last_failure_time=self._last_failure_time,
                last_success_time=self._last_success_time,
            )

    def _on_success(self) -> None:
        """Handle a successful request."""
        self._last_success_time = time.monotonic()
        self._success_count += 1

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle a failed request."""
        self._last_failure_time = time.monotonic()
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self._config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has elapsed to attempt a reset."""
        if self._opened_at is None:
            return False
        elapsed = time.monotonic() - self._opened_at
        return elapsed >= self._config.reset_timeout

    def _transition_to(self, state: CircuitState) -> None:
        """Transition the circuit breaker to a new state."""
        self._state = state

        if state == CircuitState.OPEN:
            self._opened_at = time.monotonic()
            self._half_open_requests = 0
        elif state == CircuitState.HALF_OPEN:
            self._half_open_requests = 0
        elif state == CircuitState.CLOSED:
            self._failure_count = 0
            self._half_open_requests = 0
            self._opened_at = None
