"""Configuration types for the Huefy SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from huefy.http.circuit_breaker import CircuitBreakerConfig
from huefy.http.retry import RetryConfig
from huefy.utils.logger import Logger


@dataclass
class HuefyConfig:
    """Configuration for the HuefyClient.

    Attributes:
        api_key: The API key for authentication (required).
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds.
        retry_config: Configuration for retry behavior.
        circuit_breaker_config: Configuration for circuit breaker behavior.
        logger: Custom logger instance.
        secondary_api_key: Fallback API key for key rotation.
        enable_request_signing: Enable HMAC request signing.
        enable_error_sanitization: Enable error message sanitization.
    """
    api_key: str
    base_url: str | None = None
    timeout: float = 30.0
    retry_config: RetryConfig | None = None
    circuit_breaker_config: CircuitBreakerConfig | None = None
    logger: Logger | None = None
    secondary_api_key: str | None = None
    enable_request_signing: bool = False
    enable_error_sanitization: bool = False

    def to_kwargs(self) -> dict[str, Any]:
        """Convert to keyword arguments for HuefyClient constructor.

        Returns:
            A dictionary suitable for unpacking into the client constructor.
        """
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retry_config": self.retry_config,
            "circuit_breaker_config": self.circuit_breaker_config,
            "logger": self.logger,
            "secondary_api_key": self.secondary_api_key,
            "enable_request_signing": self.enable_request_signing,
            "enable_error_sanitization": self.enable_error_sanitization,
        }
