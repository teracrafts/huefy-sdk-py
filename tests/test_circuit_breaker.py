"""Tests for the circuit breaker implementation."""

from __future__ import annotations

import asyncio

import pytest

from huefy.http.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
)


@pytest.fixture
def breaker() -> CircuitBreaker:
    return CircuitBreaker(config=CircuitBreakerConfig(
        failure_threshold=3,
        reset_timeout=0.1,
        half_open_requests=1,
    ))


class TestCircuitBreakerClosed:
    """Tests for the CLOSED state."""

    async def test_successful_calls_stay_closed(self, breaker: CircuitBreaker) -> None:
        async def ok() -> str:
            return "ok"

        result = await breaker.execute(ok)
        assert result == "ok"
        assert breaker.get_state() == CircuitState.CLOSED

    async def test_failures_below_threshold_stay_closed(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        assert breaker.get_state() == CircuitState.CLOSED

    async def test_failures_at_threshold_open_circuit(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        assert breaker.get_state() == CircuitState.OPEN


class TestCircuitBreakerOpen:
    """Tests for the OPEN state."""

    async def test_rejects_requests_when_open(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        # Trip the breaker
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        # Should now reject
        with pytest.raises(CircuitOpenError):
            await breaker.execute(fail)

    async def test_transitions_to_half_open_after_timeout(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        assert breaker.get_state() == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        assert breaker.get_state() == CircuitState.HALF_OPEN


class TestCircuitBreakerHalfOpen:
    """Tests for the HALF_OPEN state."""

    async def test_success_in_half_open_closes_circuit(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        async def ok() -> str:
            return "recovered"

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        await asyncio.sleep(0.15)

        result = await breaker.execute(ok)
        assert result == "recovered"
        assert breaker.get_state() == CircuitState.CLOSED

    async def test_failure_in_half_open_reopens_circuit(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        await asyncio.sleep(0.15)

        with pytest.raises(RuntimeError):
            await breaker.execute(fail)

        assert breaker.get_state() == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Tests for resetting the circuit breaker."""

    async def test_reset_returns_to_closed(self, breaker: CircuitBreaker) -> None:
        async def fail() -> None:
            raise RuntimeError("fail")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await breaker.execute(fail)

        assert breaker.get_state() == CircuitState.OPEN

        breaker.reset()
        assert breaker.get_state() == CircuitState.CLOSED


class TestCircuitBreakerStats:
    """Tests for statistics reporting."""

    async def test_stats_track_calls(self, breaker: CircuitBreaker) -> None:
        async def ok() -> str:
            return "ok"

        await breaker.execute(ok)
        await breaker.execute(ok)

        stats = breaker.get_stats()
        assert stats.total_requests == 2
        assert stats.success_count == 2
        assert stats.failure_count == 0
        assert stats.state == CircuitState.CLOSED
