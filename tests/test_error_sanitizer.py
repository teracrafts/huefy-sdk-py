"""Tests for error message sanitization."""

from __future__ import annotations

from huefy.errors.sanitizer import ErrorSanitizationConfig, sanitize_error_message


class TestSanitizeErrorMessage:
    """Tests for the sanitize_error_message function."""

    def test_sanitizes_unix_paths(self) -> None:
        msg = "Error reading /home/user/config/secrets.json"
        result = sanitize_error_message(msg)
        assert "/home/user" not in result
        assert "[PATH_REDACTED]" in result

    def test_sanitizes_windows_paths(self) -> None:
        msg = "Error reading C:\\Users\\admin\\Documents\\secrets.txt"
        result = sanitize_error_message(msg)
        assert "C:\\Users" not in result
        assert "[PATH_REDACTED]" in result

    def test_sanitizes_ipv4_addresses(self) -> None:
        msg = "Connection refused to 192.168.1.100:8080"
        result = sanitize_error_message(msg)
        assert "192.168.1.100" not in result
        assert "[IP_REDACTED]" in result

    def test_sanitizes_email_addresses(self) -> None:
        msg = "Failed to send to admin@company.com"
        result = sanitize_error_message(msg)
        assert "admin@company.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_sanitizes_connection_strings(self) -> None:
        msg = "Failed: postgres://user:pass@host:5432/db"
        result = sanitize_error_message(msg)
        assert "postgres://user:pass" not in result
        assert "REDACTED" in result

    def test_sanitizes_mongodb_connection_strings(self) -> None:
        msg = "Error connecting to mongodb://admin:secret@cluster.example.com/mydb"
        result = sanitize_error_message(msg)
        assert "mongodb://admin:secret" not in result

    def test_empty_message_returns_empty(self) -> None:
        assert sanitize_error_message("") == ""

    def test_none_safe(self) -> None:
        # Edge case: message is falsy
        assert sanitize_error_message("") == ""

    def test_message_without_sensitive_data_unchanged(self) -> None:
        msg = "Request failed with status 500"
        result = sanitize_error_message(msg)
        assert result == msg

    def test_selective_sanitization_paths_only(self) -> None:
        msg = "Error at /home/user/app reading from 192.168.1.1"
        config = ErrorSanitizationConfig(
            sanitize_paths=True,
            sanitize_ips=False,
            sanitize_keys=False,
            sanitize_emails=False,
            sanitize_connection_strings=False,
        )
        result = sanitize_error_message(msg, config=config)
        assert "[PATH_REDACTED]" in result
        # IP should not be redacted since sanitize_ips=False
        assert "192.168.1.1" in result

    def test_custom_patterns(self) -> None:
        msg = "Error: order-12345 failed"
        config = ErrorSanitizationConfig(
            custom_patterns=[
                (r"order-\d+", "[ORDER_REDACTED]"),
            ],
        )
        result = sanitize_error_message(msg, config=config)
        assert "order-12345" not in result
        assert "[ORDER_REDACTED]" in result

    def test_invalid_custom_pattern_is_ignored(self) -> None:
        msg = "Some error message"
        config = ErrorSanitizationConfig(
            custom_patterns=[
                (r"[invalid", "[REDACTED]"),  # Invalid regex
            ],
        )
        # Should not raise, just skip the invalid pattern
        result = sanitize_error_message(msg, config=config)
        assert result == msg
