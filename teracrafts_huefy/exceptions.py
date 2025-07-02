"""Exception classes for the Huefy SDK."""

from typing import Any, Dict, List, Optional


class HuefyError(Exception):
    """Base exception class for all Huefy SDK exceptions.

    This is the parent class for all exceptions thrown by the Huefy SDK.
    It provides a common interface for handling errors and includes support
    for error chaining and detailed error information.

    Attributes:
        message: Error message
        code: Optional error code
        details: Optional additional error details
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize HuefyError.

        Args:
            message: Error message
            code: Optional error code
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.code:
            return f"Huefy API error [{self.code}]: {self.message}"
        return f"Huefy API error: {self.message}"

    def __repr__(self) -> str:
        """Detailed string representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r})"
        )


class AuthenticationError(HuefyError):
    """Exception thrown when authentication fails.

    This exception is thrown when the API key is invalid, expired,
    or when there are other authentication-related issues.
    """

    pass


class TemplateNotFoundError(HuefyError):
    """Exception thrown when a specified email template is not found.

    This exception is thrown when attempting to send an email using
    a template key that doesn't exist in the Huefy system.

    Attributes:
        template_key: The template key that was not found
    """

    def __init__(
        self,
        message: str,
        template_key: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize TemplateNotFoundError.

        Args:
            message: Error message
            template_key: The template key that was not found
            code: Optional error code
            details: Optional additional error details
        """
        super().__init__(message, code, details)
        self.template_key = template_key


class InvalidTemplateDataError(HuefyError):
    """Exception thrown when template data validation fails.

    This exception is thrown when the data provided for a template
    doesn't match the template's requirements, such as missing required
    fields or invalid data types.

    Attributes:
        validation_errors: List of validation error messages
    """

    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize InvalidTemplateDataError.

        Args:
            message: Error message
            validation_errors: List of validation error messages
            code: Optional error code
            details: Optional additional error details
        """
        super().__init__(message, code, details)
        self.validation_errors = validation_errors or []


class InvalidRecipientError(HuefyError):
    """Exception thrown when a recipient email address is invalid.

    This exception is thrown when the recipient email address
    is malformed, empty, or otherwise invalid according to email
    address validation rules.
    """

    pass


class ProviderError(HuefyError):
    """Exception thrown when an email provider rejects or fails to send an email.

    This exception is thrown when the underlying email provider
    (SES, SendGrid, Mailgun, etc.) encounters an error or rejects
    the email for provider-specific reasons.

    Attributes:
        provider: The email provider that encountered the error
        provider_code: Provider-specific error code
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        provider_code: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ProviderError.

        Args:
            message: Error message
            provider: The email provider that encountered the error
            provider_code: Provider-specific error code
            code: Optional error code
            details: Optional additional error details
        """
        super().__init__(message, code, details)
        self.provider = provider
        self.provider_code = provider_code


class RateLimitError(HuefyError):
    """Exception thrown when API rate limits are exceeded.

    This exception is thrown when the client has exceeded the
    allowed number of requests per time period. It includes information
    about when the client can retry the request.

    Attributes:
        retry_after: Number of seconds to wait before retrying
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message
            retry_after: Number of seconds to wait before retrying
            code: Optional error code
            details: Optional additional error details
        """
        super().__init__(message, code, details)
        self.retry_after = retry_after


class NetworkError(HuefyError):
    """Exception thrown when network-related errors occur.

    This exception is thrown when there are connectivity issues,
    DNS resolution failures, or other network-related problems that
    prevent communication with the Huefy API.
    """

    pass


class TimeoutError(HuefyError):
    """Exception thrown when API requests timeout.

    This exception is thrown when a request to the Huefy API
    takes longer than the configured timeout period to complete.
    """

    pass


class ValidationError(HuefyError):
    """Exception thrown when request validation fails.

    This exception is thrown when the request data doesn't meet
    the API's validation requirements, such as missing required fields
    or invalid parameter values.
    """

    pass


def create_error_from_response(
    error_data: Dict[str, Any], status_code: int
) -> HuefyError:
    """Create appropriate exception types from error responses.

    Args:
        error_data: Error response data
        status_code: HTTP status code

    Returns:
        HuefyError: Appropriate exception based on error data
    """
    error_detail = error_data.get("error", {})
    code = error_detail.get("code", "")
    message = error_detail.get("message", "Unknown error")
    details = error_detail.get("details", {})

    # Create specific error types based on error code
    if code == "AUTHENTICATION_FAILED":
        return AuthenticationError(message, code=code, details=details)
    elif code == "TEMPLATE_NOT_FOUND":
        template_key = details.get("templateKey")
        return TemplateNotFoundError(
            message, template_key=template_key, code=code, details=details
        )
    elif code == "INVALID_TEMPLATE_DATA":
        validation_errors = details.get("validationErrors", [])
        return InvalidTemplateDataError(
            message, validation_errors=validation_errors, code=code, details=details
        )
    elif code == "INVALID_RECIPIENT":
        return InvalidRecipientError(message, code=code, details=details)
    elif code == "PROVIDER_ERROR":
        provider = details.get("provider")
        provider_code = details.get("providerCode")
        return ProviderError(
            message,
            provider=provider,
            provider_code=provider_code,
            code=code,
            details=details,
        )
    elif code == "RATE_LIMIT_EXCEEDED":
        retry_after = details.get("retryAfter")
        return RateLimitError(
            message, retry_after=retry_after, code=code, details=details
        )
    elif code == "VALIDATION_FAILED":
        return ValidationError(message, code=code, details=details)
    elif code == "TIMEOUT":
        return TimeoutError(message, code=code, details=details)
    elif code == "NETWORK_ERROR":
        return NetworkError(message, code=code, details=details)
    else:
        # Return generic HuefyError for unknown error codes
        return HuefyError(message, code=code, details=details)