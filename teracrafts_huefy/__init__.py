"""Huefy Python SDK.

The official Python SDK for the Huefy email sending platform.
Send template-based emails with support for multiple providers,
automatic retries, and comprehensive error handling.

Basic usage:
    >>> from teracrafts_huefy import HuefyClient
    >>> client = HuefyClient("your-api-key")
    >>> response = client.send_email(
    ...     template_key="welcome-email",
    ...     recipient="john@example.com",
    ...     data={"name": "John Doe", "company": "Acme Corp"}
    ... )
    >>> print(f"Email sent: {response.message_id}")
"""

from .client import HuefyClient
from .exceptions import (
    HuefyError,
    AuthenticationError,
    TemplateNotFoundError,
    InvalidTemplateDataError,
    InvalidRecipientError,
    ProviderError,
    RateLimitError,
    NetworkError,
    TimeoutError,
    ValidationError,
)
from .models import (
    EmailProvider,
    SendEmailRequest,
    SendEmailResponse,
    BulkEmailResponse,
    HealthResponse,
)
from .config import HuefyConfig, RetryConfig

__version__ = "1.0.0-beta.10"
__author__ = "Huefy Team"
__email__ = "developers@huefy.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2024 Huefy"

__all__ = [
    # Main client
    "HuefyClient",
    # Configuration
    "HuefyConfig",
    "RetryConfig",
    # Models
    "EmailProvider",
    "SendEmailRequest",
    "SendEmailResponse",
    "BulkEmailResponse",
    "HealthResponse",
    # Exceptions
    "HuefyError",
    "AuthenticationError",
    "TemplateNotFoundError",
    "InvalidTemplateDataError",
    "InvalidRecipientError",
    "ProviderError",
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
    "ValidationError",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
]