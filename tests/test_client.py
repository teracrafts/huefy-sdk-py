"""Tests for the Huefy client."""

import pytest
import responses
from datetime import datetime
from requests.exceptions import ConnectionError, Timeout

from teracrafts_huefy import (
    HuefyClient,
    HuefyConfig,
    RetryConfig,
    EmailProvider,
    SendEmailRequest,
    AuthenticationError,
    TemplateNotFoundError,
    RateLimitError,
    NetworkError,
    TimeoutError,
    ValidationError,
)


class TestHuefyClient:
    """Test cases for HuefyClient."""

    def test_init_with_valid_api_key(self):
        """Test client initialization with valid API key."""
        client = HuefyClient("test-api-key")
        assert client._api_key == "test-api-key"
        assert isinstance(client._config, HuefyConfig)

    def test_init_with_custom_config(self):
        """Test client initialization with custom config."""
        config = HuefyConfig(
            base_url="https://custom.api.com",
            connect_timeout=15.0,
            retry_config=RetryConfig(max_retries=5),
        )
        client = HuefyClient("test-api-key", config)
        assert client._config.base_url == "https://custom.api.com"
        assert client._config.connect_timeout == 15.0
        assert client._config.retry_config.max_retries == 5

    def test_init_with_none_api_key(self):
        """Test client initialization with None API key."""
        with pytest.raises(ValueError, match="API key cannot be None or empty"):
            HuefyClient(None)

    def test_init_with_empty_api_key(self):
        """Test client initialization with empty API key."""
        with pytest.raises(ValueError, match="API key cannot be None or empty"):
            HuefyClient("")

    def test_init_with_whitespace_api_key(self):
        """Test client initialization with whitespace API key."""
        with pytest.raises(ValueError, match="API key cannot be None or empty"):
            HuefyClient("   ")

    @responses.activate
    def test_send_email_success(self):
        """Test successful email sending."""
        # Setup mock response
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/send",
            json={
                "messageId": "msg-123",
                "status": "sent",
                "provider": "ses",
                "timestamp": "2024-01-01T12:00:00Z",
            },
            status=200,
        )

        client = HuefyClient("test-api-key")
        response = client.send_email(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe"},
        )

        assert response.message_id == "msg-123"
        assert response.status == "sent"
        assert response.provider == EmailProvider.SES
        assert len(responses.calls) == 1

        # Verify request headers
        request = responses.calls[0].request
        assert request.headers["X-API-Key"] == "test-api-key"
        assert request.headers["Content-Type"] == "application/json"
        assert "Huefy-Python-SDK" in request.headers["User-Agent"]

    @responses.activate
    def test_send_email_with_provider(self):
        """Test email sending with specific provider."""
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/send",
            json={
                "messageId": "msg-456",
                "status": "sent",
                "provider": "sendgrid",
                "timestamp": "2024-01-01T12:00:00Z",
            },
            status=200,
        )

        client = HuefyClient("test-api-key")
        response = client.send_email(
            template_key="welcome-email",
            recipient="john@example.com",
            data={"name": "John Doe"},
            provider=EmailProvider.SENDGRID,
        )

        assert response.provider == EmailProvider.SENDGRID

    def test_send_email_validation_error(self):
        """Test email sending with validation error."""
        client = HuefyClient("test-api-key")

        with pytest.raises(ValueError, match="Template key is required"):
            client.send_email(
                template_key="",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )

        with pytest.raises(ValueError, match="Invalid email address"):
            client.send_email(
                template_key="welcome-email",
                recipient="invalid-email",
                data={"name": "John Doe"},
            )

        with pytest.raises(ValueError, match="Template data is required"):
            client.send_email(
                template_key="welcome-email",
                recipient="john@example.com",
                data={},
            )

    @responses.activate
    def test_send_email_authentication_error(self):
        """Test email sending with authentication error."""
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/send",
            json={
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": "Invalid API key",
                }
            },
            status=401,
        )

        client = HuefyClient("invalid-api-key")
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            client.send_email(
                template_key="welcome-email",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )

    @responses.activate
    def test_send_email_template_not_found_error(self):
        """Test email sending with template not found error."""
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/send",
            json={
                "error": {
                    "code": "TEMPLATE_NOT_FOUND",
                    "message": "Template not found: nonexistent-template",
                    "details": {"templateKey": "nonexistent-template"},
                }
            },
            status=404,
        )

        client = HuefyClient("test-api-key")
        with pytest.raises(TemplateNotFoundError) as exc_info:
            client.send_email(
                template_key="nonexistent-template",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )

        assert exc_info.value.template_key == "nonexistent-template"

    @responses.activate
    def test_send_email_rate_limit_error(self):
        """Test email sending with rate limit error."""
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/send",
            json={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded",
                    "details": {"retryAfter": 60},
                }
            },
            status=429,
        )

        client = HuefyClient("test-api-key")
        with pytest.raises(RateLimitError) as exc_info:
            client.send_email(
                template_key="welcome-email",
                recipient="john@example.com",
                data={"name": "John Doe"},
            )

        assert exc_info.value.retry_after == 60

    @responses.activate
    def test_send_bulk_emails_success(self):
        """Test successful bulk email sending."""
        responses.add(
            responses.POST,
            "https://api.huefy.com/api/v1/sdk/emails/bulk",
            json={
                "results": [
                    {
                        "success": True,
                        "result": {
                            "messageId": "msg-123",
                            "status": "sent",
                            "provider": "ses",
                            "timestamp": "2024-01-01T12:00:00Z",
                        },
                        "error": None,
                    },
                    {
                        "success": True,
                        "result": {
                            "messageId": "msg-456",
                            "status": "sent",
                            "provider": "ses",
                            "timestamp": "2024-01-01T12:00:00Z",
                        },
                        "error": None,
                    },
                ]
            },
            status=200,
        )

        requests = [
            SendEmailRequest(
                template_key="welcome-email",
                recipient="john@example.com",
                data={"name": "John Doe"},
            ),
            SendEmailRequest(
                template_key="welcome-email",
                recipient="jane@example.com",
                data={"name": "Jane Doe"},
            ),
        ]

        client = HuefyClient("test-api-key")
        response = client.send_bulk_emails(requests)

        assert len(response.results) == 2
        assert all(result.success for result in response.results)
        assert response.results[0].result.message_id == "msg-123"
        assert response.results[1].result.message_id == "msg-456"

    def test_send_bulk_emails_empty_list(self):
        """Test bulk email sending with empty list."""
        client = HuefyClient("test-api-key")
        with pytest.raises(ValueError, match="Requests list cannot be empty"):
            client.send_bulk_emails([])

    def test_send_bulk_emails_invalid_request(self):
        """Test bulk email sending with invalid request in list."""
        requests = [
            SendEmailRequest(
                template_key="welcome-email",
                recipient="john@example.com",
                data={"name": "John Doe"},
            ),
            SendEmailRequest(
                template_key="welcome-email",
                recipient="invalid-email",  # Invalid email
                data={"name": "Jane Doe"},
            ),
        ]

        client = HuefyClient("test-api-key")
        with pytest.raises(ValidationError, match="Validation failed for request 1"):
            client.send_bulk_emails(requests)

    @responses.activate
    def test_health_check_success(self):
        """Test successful health check."""
        responses.add(
            responses.GET,
            "https://api.huefy.com/api/v1/sdk/health",
            json={
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0.0",
            },
            status=200,
        )

        client = HuefyClient("test-api-key")
        response = client.health_check()

        assert response.status == "healthy"
        assert response.version == "1.0.0"

    def test_network_error(self):
        """Test network error handling."""
        client = HuefyClient("test-api-key")
        
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.huefy.com/api/v1/sdk/emails/send",
                body=ConnectionError("Connection failed"),
            )
            
            with pytest.raises(NetworkError, match="Connection error occurred"):
                client.send_email(
                    template_key="welcome-email",
                    recipient="john@example.com",
                    data={"name": "John Doe"},
                )

    def test_timeout_error(self):
        """Test timeout error handling."""
        client = HuefyClient("test-api-key")
        
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.huefy.com/api/v1/sdk/emails/send",
                body=Timeout("Request timed out"),
            )
            
            with pytest.raises(TimeoutError, match="Request timed out"):
                client.send_email(
                    template_key="welcome-email",
                    recipient="john@example.com",
                    data={"name": "John Doe"},
                )

    def test_context_manager(self):
        """Test client as context manager."""
        with HuefyClient("test-api-key") as client:
            assert isinstance(client, HuefyClient)
        # Client should be closed after exiting context

    def test_close(self):
        """Test client close method."""
        client = HuefyClient("test-api-key")
        client.close()  # Should not raise any exceptions