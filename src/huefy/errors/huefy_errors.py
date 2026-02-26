"""Huefy email-specific error classes."""

from __future__ import annotations

from typing import Any, Dict, Optional


class HuefyDomainError(Exception):
    """Base error for Huefy email domain operations."""

    def __init__(
        self,
        message: str,
        code: str = "UNEXPECTED_ERROR",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details


class AuthenticationError(HuefyDomainError):
    def __init__(self, message: str = "Invalid or missing API key", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_API_KEY", 401, details)


class TemplateNotFoundError(HuefyDomainError):
    def __init__(self, template_key: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Template not found: {template_key}", "TEMPLATE_NOT_FOUND", 404, details)
        self.template_key = template_key


class InvalidTemplateDataError(HuefyDomainError):
    def __init__(self, message: str = "Invalid template data", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_TEMPLATE_DATA", 400, details)


class InvalidRecipientError(HuefyDomainError):
    def __init__(self, recipient: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Invalid recipient email: {recipient}", "INVALID_RECIPIENT", 400, details)


class ProviderError(HuefyDomainError):
    def __init__(self, message: str = "Email provider error", provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PROVIDER_ERROR", 500, details)
        self.provider = provider


class RateLimitError(HuefyDomainError):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429, details)
        self.retry_after = retry_after


def create_error_from_response(error_data: Dict[str, Any], status_code: int) -> HuefyDomainError:
    code = error_data.get("code", "")
    message = error_data.get("error", error_data.get("message", "Unknown error"))
    details = error_data.get("details")

    error_map = {
        "INVALID_API_KEY": lambda: AuthenticationError(message, details),
        "AUTHENTICATION_FAILED": lambda: AuthenticationError(message, details),
        "TEMPLATE_NOT_FOUND": lambda: TemplateNotFoundError(message, details),
        "INVALID_TEMPLATE_DATA": lambda: InvalidTemplateDataError(message, details),
        "INVALID_RECIPIENT": lambda: InvalidRecipientError(message, details),
        "PROVIDER_ERROR": lambda: ProviderError(message, details=details),
        "RATE_LIMIT_EXCEEDED": lambda: RateLimitError(message, details=details),
    }

    factory = error_map.get(code)
    if factory:
        return factory()
    return HuefyDomainError(message, code or "UNEXPECTED_ERROR", status_code, details)
