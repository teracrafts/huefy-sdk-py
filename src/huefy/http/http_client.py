"""HTTP client for Huefy API requests."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from huefy.errors.huefy_error import HuefyError
from huefy.http.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from huefy.http.retry import RetryConfig, with_retry
from huefy.utils.logger import Logger
from huefy.utils.platform import get_sdk_user_agent
from huefy.utils.security import create_request_signature, get_key_id


BASE_URL = "https://api.huefy.dev/api/v1/sdk"
LOCAL_BASE_URL = "https://api.huefy.on/api/v1/sdk"


class HttpClient:
    """Low-level HTTP client that handles authentication, retries, circuit breaking,
    and request signing for all API requests.
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
        self._api_key = api_key
        self._secondary_api_key = secondary_api_key
        self._base_url = base_url
        self._timeout = timeout
        self._retry_config = retry_config or RetryConfig()
        self._logger = logger
        self._enable_request_signing = enable_request_signing
        self._enable_error_sanitization = enable_error_sanitization

        cb_config = circuit_breaker_config or CircuitBreakerConfig()
        self._circuit_breaker = CircuitBreaker(config=cb_config)

        self._client = httpx.AsyncClient(timeout=timeout)

    def get_base_url(self) -> str:
        """Resolve the base URL based on configuration and environment."""
        if self._base_url:
            return self._base_url

        mode = os.environ.get("HUEFY_MODE", "").lower()
        if mode == "local" or mode == "development":
            return LOCAL_BASE_URL

        return BASE_URL

    async def request(
        self,
        path: str,
        *,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout: float | None = None,
        skip_retry: bool = False,
    ) -> dict[str, Any]:
        """Make an authenticated HTTP request to the API.

        Args:
            path: The API endpoint path.
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            headers: Additional headers to include.
            body: Request body for POST/PUT/PATCH requests.
            timeout: Override the default timeout for this request.
            skip_retry: If True, do not use retry logic.

        Returns:
            The parsed JSON response body.

        Raises:
            HuefyError: On network, authentication, timeout, or API errors.
        """
        url = f"{self.get_base_url()}{path}"
        request_headers = self._build_headers(
            api_key=self._api_key,
            extra_headers=headers,
            body=body,
        )

        async def do_request() -> dict[str, Any]:
            return await self._execute_request(
                url=url,
                method=method,
                headers=request_headers,
                body=body,
                timeout=timeout or self._timeout,
            )

        async def execute_with_circuit_breaker() -> dict[str, Any]:
            return await self._circuit_breaker.execute(do_request)

        if skip_retry:
            return await execute_with_circuit_breaker()

        return await with_retry(
            execute_with_circuit_breaker,
            config=self._retry_config,
            logger=self._logger,
        )

    async def _execute_request(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout: float,
    ) -> dict[str, Any]:
        """Execute a single HTTP request with key rotation on 401."""
        try:
            response = await self._send(url, method, headers, body, timeout)

            # Key rotation: on 401, retry with secondary API key
            if response.status_code == 401 and self._secondary_api_key:
                if self._logger:
                    self._logger.warn("Primary API key rejected, rotating to secondary key")
                rotated_headers = self._build_headers(
                    api_key=self._secondary_api_key,
                    extra_headers=None,
                    body=body,
                )
                # Merge any extra headers that were in the original
                for key, value in headers.items():
                    if key not in ("X-API-Key", "X-Signature", "X-Timestamp", "X-Key-Id"):
                        rotated_headers[key] = value
                response = await self._send(url, method, rotated_headers, body, timeout)

            return self._handle_response(response)

        except httpx.TimeoutException as exc:
            raise HuefyError.timeout_error(
                url=url,
                timeout=timeout,
            ) from exc
        except httpx.ConnectError as exc:
            raise HuefyError.network_error(
                message=f"Connection failed: {exc}",
                url=url,
            ) from exc
        except httpx.HTTPError as exc:
            raise HuefyError.network_error(
                message=f"HTTP error: {exc}",
                url=url,
            ) from exc

    async def _send(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout: float,
    ) -> httpx.Response:
        """Send the raw HTTP request via httpx."""
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers,
            "timeout": timeout,
        }
        if body is not None:
            request_kwargs["content"] = json.dumps(body)
            if "Content-Type" not in headers:
                request_kwargs["headers"]["Content-Type"] = "application/json"

        return await self._client.request(**request_kwargs)

    def _build_headers(
        self,
        api_key: str,
        extra_headers: dict[str, str] | None,
        body: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Build the full set of request headers."""
        headers: dict[str, str] = {
            "X-API-Key": api_key,
            "User-Agent": get_sdk_user_agent(),
            "Accept": "application/json",
        }

        if self._enable_request_signing and body is not None:
            signature_data = create_request_signature(body, api_key)
            headers["X-Signature"] = signature_data["signature"]
            headers["X-Timestamp"] = signature_data["timestamp"]
            headers["X-Key-Id"] = get_key_id(api_key)

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Parse and validate the HTTP response."""
        if response.status_code >= 400:
            try:
                body = response.json()
            except (json.JSONDecodeError, ValueError):
                body = {"message": response.text or "Unknown error"}

            raise HuefyError.from_response(
                status_code=response.status_code,
                body=body,
            )

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return {"data": response.text}

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
