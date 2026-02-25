"""Error message sanitization to prevent leaking sensitive data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ErrorSanitizationConfig:
    """Configuration for error message sanitization.

    Attributes:
        sanitize_paths: Remove file system paths from error messages.
        sanitize_ips: Remove IP addresses from error messages.
        sanitize_keys: Remove API keys and tokens from error messages.
        sanitize_emails: Remove email addresses from error messages.
        sanitize_connection_strings: Remove database/service connection strings.
        custom_patterns: Additional regex patterns to sanitize.
    """
    sanitize_paths: bool = True
    sanitize_ips: bool = True
    sanitize_keys: bool = True
    sanitize_emails: bool = True
    sanitize_connection_strings: bool = True
    custom_patterns: list[tuple[str, str]] = field(default_factory=list)


# Pre-compiled sanitization patterns
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # File system paths (Unix and Windows)
    (re.compile(r"/(?:home|usr|var|etc|tmp|opt|Users|mnt)/[\w./-]+"), "[PATH_REDACTED]"),
    (re.compile(r"[A-Za-z]:\\[\w.\\/-]+"), "[PATH_REDACTED]"),

    # IPv4 addresses
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP_REDACTED]"),

    # IPv6 addresses (simplified)
    (re.compile(r"\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7}\b"), "[IP_REDACTED]"),

    # API keys and tokens (common patterns)
    (re.compile(r"\b(?:sk|pk|api|key|token|secret|bearer)[-_][\w]{16,}\b", re.IGNORECASE), "[KEY_REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9]{32,}\b"), "[KEY_REDACTED]"),

    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),

    # Connection strings
    (re.compile(
        r"(?:mongodb|postgres|postgresql|mysql|redis|amqp|mssql)://[^\s,;]+",
        re.IGNORECASE,
    ), "[CONNECTION_STRING_REDACTED]"),

    # Generic URIs with credentials
    (re.compile(r"[a-zA-Z]+://[^@\s]+@[^\s]+"), "[URI_REDACTED]"),
]

# Categorized pattern indices for selective sanitization
_PATH_PATTERNS = {0, 1}
_IP_PATTERNS = {2, 3}
_KEY_PATTERNS = {4, 5}
_EMAIL_PATTERNS = {6}
_CONNECTION_PATTERNS = {7, 8}


def sanitize_error_message(
    message: str,
    config: ErrorSanitizationConfig | None = None,
) -> str:
    """Sanitize an error message by removing sensitive information.

    Args:
        message: The error message to sanitize.
        config: Sanitization configuration. Uses defaults if not provided.

    Returns:
        The sanitized error message with sensitive data redacted.
    """
    if not message:
        return message

    sanitization_config = config or ErrorSanitizationConfig()
    result = message

    for idx, (pattern, replacement) in enumerate(_PATTERNS):
        should_apply = (
            (idx in _PATH_PATTERNS and sanitization_config.sanitize_paths)
            or (idx in _IP_PATTERNS and sanitization_config.sanitize_ips)
            or (idx in _KEY_PATTERNS and sanitization_config.sanitize_keys)
            or (idx in _EMAIL_PATTERNS and sanitization_config.sanitize_emails)
            or (idx in _CONNECTION_PATTERNS and sanitization_config.sanitize_connection_strings)
        )
        if should_apply:
            result = pattern.sub(replacement, result)

    # Apply custom patterns
    for custom_pattern_str, custom_replacement in sanitization_config.custom_patterns:
        try:
            custom_pattern = re.compile(custom_pattern_str)
            result = custom_pattern.sub(custom_replacement, result)
        except re.error:
            pass

    return result
