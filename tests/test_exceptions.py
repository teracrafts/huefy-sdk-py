"""Tests for Huefy exceptions."""

import pytest

from teracrafts_huefy.exceptions import (
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
    create_error_from_response,
)


class TestHuefyError:
    """Test cases for HuefyError base exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = HuefyError("Test error message")
        assert str(error) == "Huefy API error: Test error message"
        assert error.message == "Test error message"
        assert error.code is None
        assert error.details == {}

    def test_error_with_code(self):
        """Test error with error code."""
        error = HuefyError("Test error", code="TEST_ERROR")
        assert str(error) == "Huefy API error [TEST_ERROR]: Test error"
        assert error.code == "TEST_ERROR"

    def test_error_with_details(self):
        """Test error with additional details."""
        details = {"field": "value", "count": 123}
        error = HuefyError("Test error", details=details)
        assert error.details == details

    def test_error_repr(self):
        """Test error representation."""
        error = HuefyError(
            "Test error", code="TEST_ERROR", details={"key": "value"}
        )
        expected = (
            "HuefyError(message='Test error', "
            "code='TEST_ERROR', "
            "details={'key': 'value'})"
        )
        assert repr(error) == expected


class TestSpecificErrors:
    """Test cases for specific error types."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, HuefyError)
        assert str(error) == "Huefy API error: Invalid API key"

    def test_template_not_found_error(self):
        """Test TemplateNotFoundError."""
        error = TemplateNotFoundError(
            "Template not found", template_key="missing-template"
        )
        assert isinstance(error, HuefyError)
        assert error.template_key == "missing-template"

    def test_invalid_template_data_error(self):
        """Test InvalidTemplateDataError."""
        validation_errors = ["name is required", "email is invalid"]
        error = InvalidTemplateDataError(
            "Validation failed", validation_errors=validation_errors
        )
        assert isinstance(error, HuefyError)
        assert error.validation_errors == validation_errors

    def test_invalid_recipient_error(self):
        """Test InvalidRecipientError."""
        error = InvalidRecipientError("Invalid email format")
        assert isinstance(error, HuefyError)
        assert str(error) == "Huefy API error: Invalid email format"

    def test_provider_error(self):
        """Test ProviderError."""
        error = ProviderError(
            "Provider rejected email",
            provider="ses",
            provider_code="MessageRejected",
        )
        assert isinstance(error, HuefyError)
        assert error.provider == "ses"
        assert error.provider_code == "MessageRejected"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert isinstance(error, HuefyError)
        assert error.retry_after == 60

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed")
        assert isinstance(error, HuefyError)
        assert str(error) == "Huefy API error: Connection failed"

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timed out")
        assert isinstance(error, HuefyError)
        assert str(error) == "Huefy API error: Request timed out"

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid request data")
        assert isinstance(error, HuefyError)
        assert str(error) == "Huefy API error: Invalid request data"


class TestCreateErrorFromResponse:
    """Test cases for error creation from API responses."""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError from response."""
        error_data = {
            "error": {
                "code": "AUTHENTICATION_FAILED",
                "message": "Invalid API key",
            }
        }
        
        error = create_error_from_response(error_data, 401)
        assert isinstance(error, AuthenticationError)
        assert error.message == "Invalid API key"
        assert error.code == "AUTHENTICATION_FAILED"

    def test_template_not_found_error_creation(self):
        """Test creating TemplateNotFoundError from response."""
        error_data = {
            "error": {
                "code": "TEMPLATE_NOT_FOUND",
                "message": "Template not found",
                "details": {"templateKey": "missing-template"},
            }
        }
        
        error = create_error_from_response(error_data, 404)
        assert isinstance(error, TemplateNotFoundError)
        assert error.template_key == "missing-template"

    def test_invalid_template_data_error_creation(self):
        """Test creating InvalidTemplateDataError from response."""
        error_data = {
            "error": {
                "code": "INVALID_TEMPLATE_DATA",
                "message": "Validation failed",
                "details": {
                    "validationErrors": ["name is required", "email is invalid"]
                },
            }
        }
        
        error = create_error_from_response(error_data, 400)
        assert isinstance(error, InvalidTemplateDataError)
        assert error.validation_errors == ["name is required", "email is invalid"]

    def test_provider_error_creation(self):
        """Test creating ProviderError from response."""
        error_data = {
            "error": {
                "code": "PROVIDER_ERROR",
                "message": "Provider rejected email",
                "details": {
                    "provider": "ses",
                    "providerCode": "MessageRejected",
                },
            }
        }
        
        error = create_error_from_response(error_data, 400)
        assert isinstance(error, ProviderError)
        assert error.provider == "ses"
        assert error.provider_code == "MessageRejected"

    def test_rate_limit_error_creation(self):
        """Test creating RateLimitError from response."""
        error_data = {
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded",
                "details": {"retryAfter": 120},
            }
        }
        
        error = create_error_from_response(error_data, 429)
        assert isinstance(error, RateLimitError)
        assert error.retry_after == 120

    def test_validation_error_creation(self):
        """Test creating ValidationError from response."""
        error_data = {
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Request validation failed",
            }
        }
        
        error = create_error_from_response(error_data, 400)
        assert isinstance(error, ValidationError)
        assert error.message == "Request validation failed"

    def test_timeout_error_creation(self):
        """Test creating TimeoutError from response."""
        error_data = {
            "error": {
                "code": "TIMEOUT",
                "message": "Request timed out",
            }
        }
        
        error = create_error_from_response(error_data, 408)
        assert isinstance(error, TimeoutError)
        assert error.message == "Request timed out"

    def test_network_error_creation(self):
        """Test creating NetworkError from response."""
        error_data = {
            "error": {
                "code": "NETWORK_ERROR",
                "message": "Network error occurred",
            }
        }
        
        error = create_error_from_response(error_data, 500)
        assert isinstance(error, NetworkError)
        assert error.message == "Network error occurred"

    def test_unknown_error_creation(self):
        """Test creating generic HuefyError for unknown codes."""
        error_data = {
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": "Unknown error occurred",
            }
        }
        
        error = create_error_from_response(error_data, 500)
        assert isinstance(error, HuefyError)
        assert not isinstance(error, (AuthenticationError, TemplateNotFoundError))
        assert error.code == "UNKNOWN_ERROR"
        assert error.message == "Unknown error occurred"

    def test_malformed_error_response(self):
        """Test handling malformed error response."""
        error_data = {"malformed": "response"}
        
        error = create_error_from_response(error_data, 500)
        assert isinstance(error, HuefyError)
        assert error.message == "Unknown error"