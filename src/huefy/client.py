"""Huefy Python SDK client."""

from __future__ import annotations

from typing import Any

from huefy.http.http_client import HttpClient
from huefy.http.retry import RetryConfig
from huefy.http.circuit_breaker import CircuitBreakerConfig
from huefy.utils.logger import Logger, create_logger


class HuefyClient:
    """Main client for the Huefy API.

    Usage:
        async with HuefyClient(api_key="your-api-key") as client:
            result = await client.health_check()
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        logger: Logger | None = None,
        secondary_api_key: str | None = None,
        enable_request_signing: bool = False,
        enable_error_sanitization: bool = False,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self._api_key = api_key
        self._secondary_api_key = secondary_api_key
        self._base_url = base_url
        self._timeout = timeout
        self._retry_config = retry_config
        self._enable_request_signing = enable_request_signing
        self._enable_error_sanitization = enable_error_sanitization
        self._logger = logger or create_logger(debug=False)

        self._http_client = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config,
            logger=self._logger,
            secondary_api_key=secondary_api_key,
            enable_request_signing=enable_request_signing,
            enable_error_sanitization=enable_error_sanitization,
        )

        self._logger.debug("HuefyClient initialized")

    async def health_check(self) -> dict[str, Any]:
        """Check the API health status.

        Returns:
            A dictionary containing the health status response.
        """
        response = await self._http_client.request("/health", method="GET")
        return response

    def get_config(self) -> dict[str, Any]:
        """Get the current client configuration (without sensitive data).

        Returns:
            A dictionary containing the current configuration.
        """
        return {
            "base_url": self._http_client.get_base_url(),
            "timeout": self._timeout,
            "retry_config": {
                "max_retries": (self._retry_config.max_retries if self._retry_config else 3),
                "base_delay": (self._retry_config.base_delay if self._retry_config else 1.0),
                "max_delay": (self._retry_config.max_delay if self._retry_config else 30.0),
            },
            "enable_request_signing": self._enable_request_signing,
            "enable_error_sanitization": self._enable_error_sanitization,
            "has_secondary_key": self._secondary_api_key is not None,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        await self._http_client.close()
        self._logger.debug("HuefyClient closed")

    async def __aenter__(self) -> HuefyClient:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        await self.close()
