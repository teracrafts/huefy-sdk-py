"""Huefy SDK error types and utilities."""

from huefy.errors.error_codes import ErrorCode, NUMERIC_CODE_MAP, is_recoverable_code
from huefy.errors.huefy_error import HuefyError
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
from huefy.errors.sanitizer import (
    ErrorSanitizationConfig,
    sanitize_error_message,
)

__all__ = [
    # Core error
    "HuefyError",
    # Error codes
    "ErrorCode",
    "NUMERIC_CODE_MAP",
    "is_recoverable_code",
    # Domain errors
    "HuefyDomainError",
    "AuthenticationError",
    "TemplateNotFoundError",
    "InvalidTemplateDataError",
    "InvalidRecipientError",
    "ProviderError",
    "RateLimitError",
    "create_error_from_response",
    # Sanitizer
    "ErrorSanitizationConfig",
    "sanitize_error_message",
]
