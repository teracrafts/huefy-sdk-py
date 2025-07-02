"""Tests for Huefy models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from teracrafts_huefy.models import (
    EmailProvider,
    SendEmailRequest,
    SendEmailResponse,
    BulkEmailResult,
    BulkEmailResponse,
    HealthResponse,
    ErrorDetail,
    ErrorResponse,
)


class TestEmailProvider:
    """Test cases for EmailProvider enum."""

    def test_all_providers(self):
        """Test all email provider values."""
        assert EmailProvider.SES == "ses"
        assert EmailProvider.SENDGRID == "sendgrid"
        assert EmailProvider.MAILGUN == "mailgun"
        assert EmailProvider.MAILCHIMP == "mailchimp"

    def test_enum_membership(self):
        """Test enum membership."""
        assert "ses" in EmailProvider
        assert "sendgrid" in EmailProvider
        assert "invalid" not in EmailProvider


class TestSendEmailRequest:
    """Test cases for SendEmailRequest model."""

    def test_valid_request(self):
        """Test creating a valid email request."""
        request = SendEmailRequest(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe", "company": "Acme Corp"},
            provider=EmailProvider.SENDGRID,
        )
        
        assert request.template_key == "welcome-email"
        assert request.recipient == "john@example.com"
        assert request.data == {"name": "John Doe", "company": "Acme Corp"}
        assert request.provider == EmailProvider.SENDGRID

    def test_request_without_provider(self):
        """Test creating request without provider."""
        request = SendEmailRequest(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe"},
        )
        
        assert request.provider is None

    def test_template_key_validation(self):
        """Test template key validation."""
        # Empty template key
        with pytest.raises(ValidationError, match="Template key is required"):
            SendEmailRequest(
                template_key="",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )
        
        # Whitespace template key
        with pytest.raises(ValidationError, match="Template key is required"):
            SendEmailRequest(
                template_key="   ",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )

    def test_recipient_validation(self):
        """Test recipient email validation."""
        # Empty recipient
        with pytest.raises(ValidationError, match="Recipient email is required"):
            SendEmailRequest(
                template_key="welcome-email",
                recipient="",
                data={"name": "John Doe"},
            )
        
        # Invalid email format
        with pytest.raises(ValidationError, match="Invalid email address"):
            SendEmailRequest(
                template_key="welcome-email",
                recipient="invalid-email",
                data={"name": "John Doe"},
            )
        
        # Valid email formats
        valid_emails = [
            "john@example.com",
            "john.doe@example.com",
            "john+test@example.co.uk",
            "user123@test-domain.org",
        ]
        
        for email in valid_emails:
            request = SendEmailRequest(
                template_key="welcome-email",
                recipient=email,
                data={"name": "John Doe"},
            )
            assert request.recipient == email

    def test_data_validation(self):
        """Test template data validation."""
        # Empty data
        with pytest.raises(ValidationError, match="Template data is required"):
            SendEmailRequest(
                template_key="welcome-email",
                recipient="john@example.com",
                data={},
            )
        
        # Valid data
        request = SendEmailRequest(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe", "age": 30, "active": True},
        )
        assert request.data == {"name": "John Doe", "age": 30, "active": True}

    def test_dict_serialization(self):
        """Test model serialization to dict."""
        request = SendEmailRequest(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe"},
            provider=EmailProvider.SES,
        )
        
        data = request.dict()
        assert data == {
            "template_key": "welcome-email",
            "recipient": "john@example.com",
            "data": {"name": "John Doe"},
            "provider": "ses",
        }


class TestSendEmailResponse:
    """Test cases for SendEmailResponse model."""

    def test_valid_response(self):
        """Test creating a valid email response."""
        timestamp = datetime.now()
        response = SendEmailResponse(
            message_id="msg-123",
            status="sent",
            provider=EmailProvider.SES,
            timestamp=timestamp,
        )
        
        assert response.message_id == "msg-123"
        assert response.status == "sent"
        assert response.provider == EmailProvider.SES
        assert response.timestamp == timestamp

    def test_parse_from_dict(self):
        """Test parsing response from dict."""
        data = {
            "message_id": "msg-456",
            "status": "queued",
            "provider": "sendgrid",
            "timestamp": "2024-01-01T12:00:00Z",
        }
        
        response = SendEmailResponse.parse_obj(data)
        assert response.message_id == "msg-456"
        assert response.status == "queued"
        assert response.provider == EmailProvider.SENDGRID
        assert isinstance(response.timestamp, datetime)


class TestBulkEmailResponse:
    """Test cases for BulkEmailResponse model."""

    def test_successful_bulk_response(self):
        """Test bulk response with all successful results."""
        timestamp = datetime.now()
        results = [
            BulkEmailResult(
                success=True,
                result=SendEmailResponse(
                    message_id="msg-123",
                    status="sent",
                    provider=EmailProvider.SES,
                    timestamp=timestamp,
                ),
                error=None,
            ),
            BulkEmailResult(
                success=True,
                result=SendEmailResponse(
                    message_id="msg-456",
                    status="sent",
                    provider=EmailProvider.SES,
                    timestamp=timestamp,
                ),
                error=None,
            ),
        ]
        
        response = BulkEmailResponse(results=results)
        assert len(response.results) == 2
        assert all(result.success for result in response.results)
        assert response.results[0].result.message_id == "msg-123"
        assert response.results[1].result.message_id == "msg-456"

    def test_mixed_bulk_response(self):
        """Test bulk response with mixed success/failure results."""
        timestamp = datetime.now()
        results = [
            BulkEmailResult(
                success=True,
                result=SendEmailResponse(
                    message_id="msg-123",
                    status="sent",
                    provider=EmailProvider.SES,
                    timestamp=timestamp,
                ),
                error=None,
            ),
            BulkEmailResult(
                success=False,
                result=None,
                error={
                    "error": {
                        "code": "INVALID_RECIPIENT",
                        "message": "Invalid email address",
                    }
                },
            ),
        ]
        
        response = BulkEmailResponse(results=results)
        assert len(response.results) == 2
        assert response.results[0].success is True
        assert response.results[1].success is False
        assert response.results[0].result is not None
        assert response.results[1].error is not None


class TestHealthResponse:
    """Test cases for HealthResponse model."""

    def test_health_response_with_version(self):
        """Test health response with version."""
        timestamp = datetime.now()
        response = HealthResponse(
            status="healthy",
            timestamp=timestamp,
            version="1.0.0",
        )
        
        assert response.status == "healthy"
        assert response.timestamp == timestamp
        assert response.version == "1.0.0"

    def test_health_response_without_version(self):
        """Test health response without version."""
        timestamp = datetime.now()
        response = HealthResponse(
            status="degraded",
            timestamp=timestamp,
        )
        
        assert response.status == "degraded"
        assert response.timestamp == timestamp
        assert response.version is None


class TestErrorModels:
    """Test cases for error models."""

    def test_error_detail(self):
        """Test ErrorDetail model."""
        detail = ErrorDetail(
            code="TEMPLATE_NOT_FOUND",
            message="Template not found",
            details={"templateKey": "missing-template"},
        )
        
        assert detail.code == "TEMPLATE_NOT_FOUND"
        assert detail.message == "Template not found"
        assert detail.details == {"templateKey": "missing-template"}

    def test_error_response(self):
        """Test ErrorResponse model."""
        error_detail = ErrorDetail(
            code="AUTHENTICATION_FAILED",
            message="Invalid API key",
        )
        error_response = ErrorResponse(error=error_detail)
        
        assert error_response.error.code == "AUTHENTICATION_FAILED"
        assert error_response.error.message == "Invalid API key"