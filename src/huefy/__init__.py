"""Huefy Python SDK."""

from huefy.client import HuefyClient
from huefy.errors.huefy_error import HuefyError
from huefy.errors.error_codes import ErrorCode
from huefy.http.retry import RetryConfig
from huefy.http.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitOpenError
from huefy.types.config import HuefyConfig
from huefy.utils.version import SDK_VERSION, get_version

# Email domain layer
from huefy.huefy_client import HuefyEmailClient
from huefy.types.email import (
    EmailProvider,
    EmailRecipient,
    SendEmailRequest,
    SendEmailResponse,
    BulkRecipient,
    SendBulkEmailsRequest,
    SendBulkEmailsResponse,
    BulkEmailResult,
    HealthResponse,
)
from huefy.errors.huefy_errors import (
    HuefyDomainError,
    AuthenticationError,
    TemplateNotFoundError,
    InvalidTemplateDataError,
    InvalidRecipientError,
    ProviderError,
    RateLimitError,
    create_error_from_response,
)
from huefy.validators.email_validators import (
    validate_email,
    validate_template_key,
    validate_send_email_input,
)

__all__ = [
    "HuefyClient",
    "HuefyConfig",
    "HuefyError",
    "ErrorCode",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "SDK_VERSION",
    "get_version",
    # Email domain layer
    "HuefyEmailClient",
    "EmailProvider",
    "EmailRecipient",
    "SendEmailRequest",
    "SendEmailResponse",
    "BulkRecipient",
    "SendBulkEmailsRequest",
    "SendBulkEmailsResponse",
    "BulkEmailResult",
    "HealthResponse",
    "HuefyDomainError",
    "AuthenticationError",
    "TemplateNotFoundError",
    "InvalidTemplateDataError",
    "InvalidRecipientError",
    "ProviderError",
    "RateLimitError",
    "create_error_from_response",
    "validate_email",
    "validate_template_key",
    "validate_send_email_input",
]
