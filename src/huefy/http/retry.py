"""Retry logic with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import email.utils
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, TypeVar

from huefy.utils.logger import Logger

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        retryable_status_codes: HTTP status codes that trigger a retry.
    """
    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 10.0
    retryable_status_codes: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


def calculate_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Calculate the delay for a given retry attempt using exponential backoff with jitter.

    Args:
        attempt: The current retry attempt number (0-indexed).
        base_delay: The base delay in seconds.
        max_delay: The maximum delay in seconds.

    Returns:
        The calculated delay in seconds with jitter applied.
    """
    exponential_delay = base_delay * (2 ** attempt)
    capped_delay = min(exponential_delay, max_delay)
    jitter_factor = random.uniform(0.8, 1.2)
    return min(capped_delay * jitter_factor, max_delay)


def parse_retry_after(header: str | None) -> float | None:
    """Parse a Retry-After header value into seconds.

    Supports both integer seconds and HTTP-date formats.

    Args:
        header: The Retry-After header value.

    Returns:
        The delay in seconds, or None if the header is invalid or absent.
    """
    if header is None:
        return None

    header = header.strip()
    if not header:
        return None

    # Try parsing as integer seconds
    try:
        value = int(header)
        if value >= 0:
            return float(value)
        return None
    except ValueError:
        pass

    # Try parsing as float seconds
    try:
        value_f = float(header)
        if value_f >= 0:
            return value_f
        return None
    except ValueError:
        pass

    # Try parsing as HTTP-date (RFC 7231)
    try:
        dt = email.utils.parsedate_to_datetime(header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delay = (dt - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delay)
    except (TypeError, ValueError):
        pass

    return None


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    config: RetryConfig | None = None,
    logger: Logger | None = None,
) -> T:
    """Execute an async function with retry logic.

    Args:
        fn: The async callable to execute.
        config: Retry configuration. Uses defaults if not provided.
        logger: Optional logger for retry attempts.

    Returns:
        The result of the callable.

    Raises:
        Exception: The last exception encountered after all retries are exhausted.
    """
    retry_config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(retry_config.max_retries + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exception = exc

            if attempt >= retry_config.max_retries:
                break

            if not _should_retry(exc, retry_config):
                raise

            # Check for Retry-After header in the error
            retry_after = _extract_retry_after(exc)
            if retry_after is not None:
                delay = retry_after
            else:
                delay = calculate_delay(attempt, retry_config.base_delay, retry_config.max_delay)

            if logger:
                logger.warn(
                    f"Request failed (attempt {attempt + 1}/{retry_config.max_retries + 1}), "
                    f"retrying in {delay:.1f}s: {exc}"
                )

            await asyncio.sleep(delay)

    if last_exception is None:
        raise RuntimeError("retry loop completed without setting an exception")
    raise last_exception


def _should_retry(exc: Exception, config: RetryConfig) -> bool:
    """Determine whether an exception is retryable."""
    from huefy.errors.huefy_error import HuefyError

    if isinstance(exc, HuefyError):
        if exc.status_code is not None and exc.status_code in config.retryable_status_codes:
            return True
        if exc.recoverable:
            return True

    # Retry on connection/timeout errors
    import httpx
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True

    return False


def _extract_retry_after(exc: Exception) -> float | None:
    """Extract Retry-After value from an error if available."""
    from huefy.errors.huefy_error import HuefyError

    if isinstance(exc, HuefyError) and exc.retry_after is not None:
        return exc.retry_after
    return None
