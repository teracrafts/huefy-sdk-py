"""Shared test fixtures for the Huefy Python SDK."""

from __future__ import annotations

import pytest

from huefy.http.retry import RetryConfig
from huefy.http.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from huefy.utils.logger import NoopLogger


@pytest.fixture
def api_key() -> str:
    """A test API key."""
    return "sk_test_abcdef1234567890abcdef1234567890"


@pytest.fixture
def secondary_api_key() -> str:
    """A secondary test API key."""
    return "sk_test_secondary_0987654321fedcba"


@pytest.fixture
def noop_logger() -> NoopLogger:
    """A no-op logger for silent tests."""
    return NoopLogger()


@pytest.fixture
def retry_config() -> RetryConfig:
    """A fast retry config for tests (minimal delays)."""
    return RetryConfig(
        max_retries=2,
        base_delay=0.01,
        max_delay=0.05,
    )


@pytest.fixture
def circuit_breaker_config() -> CircuitBreakerConfig:
    """A circuit breaker config with low thresholds for tests."""
    return CircuitBreakerConfig(
        failure_threshold=2,
        reset_timeout=0.1,
        half_open_requests=1,
    )


@pytest.fixture
def circuit_breaker(circuit_breaker_config: CircuitBreakerConfig) -> CircuitBreaker:
    """A circuit breaker instance for tests."""
    return CircuitBreaker(config=circuit_breaker_config)
