"""Tests for the retry logic."""

from __future__ import annotations

import pytest

from huefy.http.retry import (
    RetryConfig,
    calculate_delay,
    parse_retry_after,
    with_retry,
)
from huefy.errors.huefy_error import HuefyError
from huefy.errors.error_codes import ErrorCode


class TestCalculateDelay:
    """Tests for delay calculation."""

    def test_first_attempt_is_near_base_delay(self) -> None:
        delay = calculate_delay(attempt=0, base_delay=1.0, max_delay=30.0)
        # Base delay = 1.0, jitter adds up to 0.5, so range is [1.0, 1.5]
        assert 1.0 <= delay <= 1.5

    def test_delay_increases_with_attempts(self) -> None:
        delay_0 = calculate_delay(attempt=0, base_delay=1.0, max_delay=60.0)
        delay_2 = calculate_delay(attempt=2, base_delay=1.0, max_delay=60.0)
        # With jitter, delay_2 should generally be larger, but check the base
        # Attempt 2: base = 4.0, so min delay is 4.0
        assert delay_2 >= 4.0

    def test_delay_is_capped_at_max(self) -> None:
        delay = calculate_delay(attempt=10, base_delay=1.0, max_delay=5.0)
        # Capped at 5.0 + up to 2.5 jitter = 7.5 max
        assert delay <= 7.5


class TestParseRetryAfter:
    """Tests for Retry-After header parsing."""

    def test_integer_seconds(self) -> None:
        assert parse_retry_after("5") == 5.0

    def test_float_seconds(self) -> None:
        assert parse_retry_after("2.5") == 2.5

    def test_zero(self) -> None:
        assert parse_retry_after("0") == 0.0

    def test_negative_returns_none(self) -> None:
        assert parse_retry_after("-1") is None

    def test_none_input(self) -> None:
        assert parse_retry_after(None) is None

    def test_empty_string(self) -> None:
        assert parse_retry_after("") is None

    def test_invalid_string(self) -> None:
        assert parse_retry_after("not-a-number") is None


class TestWithRetry:
    """Tests for the with_retry function."""

    async def test_succeeds_on_first_attempt(self) -> None:
        call_count = 0

        async def succeed() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await with_retry(succeed)
        assert result == "ok"
        assert call_count == 1

    async def test_retries_on_recoverable_error(self) -> None:
        call_count = 0

        async def fail_then_succeed() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise HuefyError(
                    "Server error",
                    code=ErrorCode.API_SERVER_ERROR,
                    status_code=500,
                    recoverable=True,
                )
            return "recovered"

        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.05)
        result = await with_retry(fail_then_succeed, config=config)
        assert result == "recovered"
        assert call_count == 3

    async def test_does_not_retry_non_recoverable_error(self) -> None:
        call_count = 0

        async def auth_fail() -> str:
            nonlocal call_count
            call_count += 1
            raise HuefyError(
                "Unauthorized",
                code=ErrorCode.AUTH_INVALID_KEY,
                status_code=401,
                recoverable=False,
            )

        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.05)
        with pytest.raises(HuefyError):
            await with_retry(auth_fail, config=config)

        assert call_count == 1

    async def test_exhausts_retries_and_raises(self) -> None:
        call_count = 0

        async def always_fail() -> str:
            nonlocal call_count
            call_count += 1
            raise HuefyError(
                "Server error",
                code=ErrorCode.API_SERVER_ERROR,
                status_code=500,
                recoverable=True,
            )

        config = RetryConfig(max_retries=2, base_delay=0.01, max_delay=0.05)
        with pytest.raises(HuefyError, match="Server error"):
            await with_retry(always_fail, config=config)

        assert call_count == 3  # 1 initial + 2 retries
