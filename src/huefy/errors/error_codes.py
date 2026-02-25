"""Standardized error codes for the Huefy SDK."""

from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    """Enumeration of all SDK error codes."""

    # Initialization errors (1xxx)
    INIT_FAILED = "INIT_FAILED"
    INIT_INVALID_CONFIG = "INIT_INVALID_CONFIG"

    # Authentication errors (2xxx)
    AUTH_MISSING_KEY = "AUTH_MISSING_KEY"
    AUTH_INVALID_KEY = "AUTH_INVALID_KEY"
    AUTH_EXPIRED_KEY = "AUTH_EXPIRED_KEY"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_KEY_ROTATION_FAILED = "AUTH_KEY_ROTATION_FAILED"

    # Network errors (3xxx)
    NETWORK_ERROR = "NETWORK_ERROR"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_DNS_FAILURE = "NETWORK_DNS_FAILURE"
    NETWORK_CONNECTION_REFUSED = "NETWORK_CONNECTION_REFUSED"
    NETWORK_SSL_ERROR = "NETWORK_SSL_ERROR"

    # API errors (4xxx)
    API_ERROR = "API_ERROR"
    API_BAD_REQUEST = "API_BAD_REQUEST"
    API_NOT_FOUND = "API_NOT_FOUND"
    API_RATE_LIMITED = "API_RATE_LIMITED"
    API_SERVER_ERROR = "API_SERVER_ERROR"
    API_UNAVAILABLE = "API_UNAVAILABLE"

    # Validation errors (5xxx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_REQUIRED_FIELD = "VALIDATION_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"

    # Circuit breaker errors (6xxx)
    CIRCUIT_OPEN = "CIRCUIT_OPEN"

    # Unknown errors (9xxx)
    UNKNOWN = "UNKNOWN"


NUMERIC_CODE_MAP: dict[ErrorCode, int] = {
    # Initialization errors (1xxx)
    ErrorCode.INIT_FAILED: 1000,
    ErrorCode.INIT_INVALID_CONFIG: 1001,

    # Authentication errors (2xxx)
    ErrorCode.AUTH_MISSING_KEY: 2000,
    ErrorCode.AUTH_INVALID_KEY: 2001,
    ErrorCode.AUTH_EXPIRED_KEY: 2002,
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: 2003,
    ErrorCode.AUTH_KEY_ROTATION_FAILED: 2004,

    # Network errors (3xxx)
    ErrorCode.NETWORK_ERROR: 3000,
    ErrorCode.NETWORK_TIMEOUT: 3001,
    ErrorCode.NETWORK_DNS_FAILURE: 3002,
    ErrorCode.NETWORK_CONNECTION_REFUSED: 3003,
    ErrorCode.NETWORK_SSL_ERROR: 3004,

    # API errors (4xxx)
    ErrorCode.API_ERROR: 4000,
    ErrorCode.API_BAD_REQUEST: 4001,
    ErrorCode.API_NOT_FOUND: 4002,
    ErrorCode.API_RATE_LIMITED: 4003,
    ErrorCode.API_SERVER_ERROR: 4004,
    ErrorCode.API_UNAVAILABLE: 4005,

    # Validation errors (5xxx)
    ErrorCode.VALIDATION_ERROR: 5000,
    ErrorCode.VALIDATION_REQUIRED_FIELD: 5001,
    ErrorCode.VALIDATION_INVALID_FORMAT: 5002,

    # Circuit breaker errors (6xxx)
    ErrorCode.CIRCUIT_OPEN: 6000,

    # Unknown errors (9xxx)
    ErrorCode.UNKNOWN: 9000,
}


def is_recoverable_code(code: ErrorCode) -> bool:
    """Determine whether an error code represents a recoverable error.

    Recoverable errors are those that may succeed on retry, such as
    network issues, rate limiting, or server errors.

    Args:
        code: The error code to check.

    Returns:
        True if the error is potentially recoverable.
    """
    recoverable_codes = {
        ErrorCode.NETWORK_ERROR,
        ErrorCode.NETWORK_TIMEOUT,
        ErrorCode.NETWORK_DNS_FAILURE,
        ErrorCode.NETWORK_CONNECTION_REFUSED,
        ErrorCode.API_RATE_LIMITED,
        ErrorCode.API_SERVER_ERROR,
        ErrorCode.API_UNAVAILABLE,
        ErrorCode.CIRCUIT_OPEN,
    }
    return code in recoverable_codes
