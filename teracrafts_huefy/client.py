"""Huefy client implementation."""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import HuefyConfig, RetryConfig
from .exceptions import (
    AuthenticationError,
    HuefyError,
    InvalidRecipientError,
    InvalidTemplateDataError,
    NetworkError,
    ProviderError,
    RateLimitError,
    TemplateNotFoundError,
    TimeoutError,
    ValidationError,
    create_error_from_response,
)
from .models import (
    BulkEmailResponse,
    EmailProvider,
    HealthResponse,
    SendEmailRequest,
    SendEmailResponse,
)

logger = logging.getLogger(__name__)


class HuefyClient:
    """Main client for the Huefy email sending platform.

    The HuefyClient provides a simple interface for sending template-based emails
    through the Huefy API with support for multiple email providers, retry logic,
    and comprehensive error handling.

    Args:
        api_key: The Huefy API key
        config: Optional client configuration

    Example:
        >>> client = HuefyClient("your-api-key")
        >>> response = client.send_email(
        ...     template_key="welcome-email",
        ...     recipient="john@example.com",
        ...     data={"name": "John Doe", "company": "Acme Corp"}
        ... )
        >>> print(f"Email sent: {response.message_id}")
    """

    def __init__(self, api_key: str, config: Optional[HuefyConfig] = None) -> None:
        """Initialize the Huefy client.

        Args:
            api_key: The Huefy API key
            config: Optional client configuration

        Raises:
            ValueError: If api_key is None or empty
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be None or empty")

        self._api_key = api_key.strip()
        self._config = config or HuefyConfig()
        self._session = self._create_session()

        logger.debug("HuefyClient initialized with base URL: %s", self._config.base_url)

    def _create_session(self) -> requests.Session:
        """Create and configure HTTP session."""
        session = requests.Session()

        # Set default headers
        session.headers.update(
            {
                "X-API-Key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"Huefy-Python-SDK/{self._get_version()}",
            }
        )

        # Configure retries if enabled
        if self._config.retry_config.enabled:
            retry_strategy = Retry(
                total=self._config.retry_config.max_retries,
                backoff_factor=self._config.retry_config.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "GET"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

        return session

    def _get_version(self) -> str:
        """Get SDK version."""
        try:
            from . import __version__

            return __version__
        except ImportError:
            return "unknown"

    def send_email(
        self,
        template_key: str,
        recipient: str,
        data: Dict[str, Any],
        provider: Optional[EmailProvider] = None,
    ) -> SendEmailResponse:
        """Send a single email using a template.

        Args:
            template_key: The template key to use
            recipient: The recipient email address
            data: Template data for variable substitution
            provider: Optional email provider to use

        Returns:
            SendEmailResponse: The email response

        Raises:
            HuefyError: If the request fails
            ValidationError: If the request data is invalid
        """
        request = SendEmailRequest(
            template_key=template_key,
            recipient=recipient,
            data=data,
            provider=provider,
        )

        return self._send_email_request(request)

    def send_bulk_emails(
        self, requests: List[SendEmailRequest]
    ) -> BulkEmailResponse:
        """Send multiple emails in a single request.

        Args:
            requests: List of email requests

        Returns:
            BulkEmailResponse: The bulk email response

        Raises:
            HuefyError: If the request fails
            ValueError: If requests is empty
        """
        if not requests:
            raise ValueError("Requests list cannot be empty")

        # Validate all requests
        for i, request in enumerate(requests):
            try:
                request.validate()
            except ValidationError as e:
                raise ValidationError(f"Validation failed for request {i}: {e}")

        payload = {"emails": [req.dict() for req in requests]}
        response_data = self._make_request("POST", "/api/v1/sdk/emails/bulk", payload)
        return BulkEmailResponse.parse_obj(response_data)

    def health_check(self) -> HealthResponse:
        """Check the health status of the Huefy API.

        Returns:
            HealthResponse: The health response

        Raises:
            HuefyError: If the request fails
        """
        response_data = self._make_request("GET", "/api/v1/sdk/health")
        return HealthResponse.parse_obj(response_data)

    def _send_email_request(self, request: SendEmailRequest) -> SendEmailResponse:
        """Send an email request.

        Args:
            request: The email request

        Returns:
            SendEmailResponse: The email response

        Raises:
            HuefyError: If the request fails
        """
        request.validate()
        response_data = self._make_request(
            "POST", "/api/v1/sdk/emails/send", request.dict()
        )
        return SendEmailResponse.parse_obj(response_data)

    def _make_request(
        self, method: str, path: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Huefy API.

        Args:
            method: HTTP method
            path: API path
            data: Request data

        Returns:
            Dict[str, Any]: Response data

        Raises:
            HuefyError: If the request fails
        """
        url = urljoin(self._config.base_url, path)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                timeout=(
                    self._config.connect_timeout,
                    self._config.read_timeout,
                ),
            )

            if response.status_code >= 400:
                self._handle_error_response(response)

            return response.json()

        except requests.exceptions.Timeout as e:
            raise TimeoutError("Request timed out") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError("Connection error occurred") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {e}") from e
        except ValueError as e:
            raise HuefyError(f"Failed to parse response JSON: {e}") from e

    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: The HTTP response

        Raises:
            HuefyError: Appropriate error based on response
        """
        try:
            error_data = response.json()
        except ValueError:
            # Fallback for non-JSON error responses
            error_data = {
                "error": {
                    "code": f"HTTP_{response.status_code}",
                    "message": response.text or f"HTTP {response.status_code}",
                }
            }

        raise create_error_from_response(error_data, response.status_code)

    def close(self) -> None:
        """Close the HTTP session and release resources.

        This method should be called when the client is no longer needed.
        """
        if self._session:
            self._session.close()
            logger.debug("HuefyClient session closed")

    def __enter__(self) -> "HuefyClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()