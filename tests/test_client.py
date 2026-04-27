"""Tests for the HuefyClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from huefy.client import HuefyClient
from huefy.errors.huefy_errors import HuefyDomainError
from huefy.huefy_client import HuefyEmailClient
from huefy.http.retry import RetryConfig
from huefy.types import BulkRecipient, EmailRecipient
from huefy.utils.logger import NoopLogger


class TestClientInit:
    """Tests for client initialization."""

    def test_requires_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key is required"):
            HuefyClient(api_key="")

    def test_creates_with_valid_key(self) -> None:
        client = HuefyClient(api_key="sk_test_1234567890abcdef")
        assert client is not None

    def test_accepts_custom_config(self) -> None:
        client = HuefyClient(
            api_key="sk_test_1234567890abcdef",
            base_url="https://custom.api.com",
            timeout=60.0,
            retry_config=RetryConfig(max_retries=5),
            logger=NoopLogger(),
            enable_request_signing=True,
            enable_error_sanitization=True,
        )
        config = client.get_config()
        assert config["timeout"] == 60.0
        assert config["retry_config"]["max_retries"] == 5
        assert config["enable_request_signing"] is True
        assert config["enable_error_sanitization"] is True


class TestClientGetConfig:
    """Tests for the get_config method."""

    def test_config_does_not_expose_api_key(self) -> None:
        client = HuefyClient(api_key="sk_test_secret_key_do_not_expose")
        config = client.get_config()
        assert "api_key" not in config
        # Also ensure the key value is not in any string value
        config_str = str(config)
        assert "sk_test_secret_key_do_not_expose" not in config_str

    def test_config_shows_secondary_key_status(self) -> None:
        client = HuefyClient(
            api_key="sk_test_primary",
            secondary_api_key="sk_test_secondary",
        )
        config = client.get_config()
        assert config["has_secondary_key"] is True

    def test_config_no_secondary_key(self) -> None:
        client = HuefyClient(api_key="sk_test_primary")
        config = client.get_config()
        assert config["has_secondary_key"] is False


class TestClientContextManager:
    """Tests for async context manager support."""

    async def test_context_manager_creates_and_closes(self) -> None:
        async with HuefyClient(api_key="sk_test_ctx_manager") as client:
            assert client is not None
            config = client.get_config()
            assert "base_url" in config


class TestClientHealthCheck:
    """Tests for the health_check method."""

    async def test_health_check_calls_api(self) -> None:
        client = HuefyClient(api_key="sk_test_health")

        mock_response = {"status": "ok", "version": "1.0.0"}

        with patch.object(
            client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            result = await client.health_check()
            mock_request.assert_called_once_with("/health", method="GET")
            assert result["status"] == "ok"

        await client.close()


class TestEmailClientSendEmail:
    """Tests for the email client send_email method."""

    async def test_send_email_preserves_string_recipient(self) -> None:
        client = HuefyEmailClient(api_key="sk_test_send_email")
        mock_response = {
            "success": True,
            "correlationId": "corr-123",
            "data": {
                "emailId": "email-1",
                "status": "queued",
                "recipients": [{"email": "user@example.com", "status": "queued"}],
            },
        }

        with patch.object(
            client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.send_email(
                template_key="welcome-email",
                recipient=" user@example.com ",
                data={"first_name": "Ada"},
            )
            mock_request.assert_called_once_with(
                "/emails/send",
                method="POST",
                body={
                    "templateKey": "welcome-email",
                    "recipient": "user@example.com",
                    "data": {"first_name": "Ada"},
                },
            )

        await client.close()


class TestEmailClientSendBulkEmails:
    async def test_send_bulk_emails_rejects_blank_template_key(self) -> None:
        client = HuefyEmailClient(api_key="sk_test_send_bulk")

        with pytest.raises(HuefyDomainError, match="Template key"):
            await client.send_bulk_emails(
                template_key="   ",
                recipients=[BulkRecipient(email="user@example.com")],
            )

        await client.close()

    async def test_send_bulk_emails_rejects_invalid_recipient_type(self) -> None:
        client = HuefyEmailClient(api_key="sk_test_send_bulk")

        with pytest.raises(HuefyDomainError, match=r"recipients\[0\].*Recipient type"):
            await client.send_bulk_emails(
                template_key="welcome-email",
                recipients=[BulkRecipient(email="user@example.com", type="reply-to")],
            )

        await client.close()

    async def test_send_email_serializes_recipient_object(self) -> None:
        client = HuefyEmailClient(api_key="sk_test_send_email")
        mock_response = {
            "success": True,
            "correlationId": "corr-123",
            "data": {
                "emailId": "email-1",
                "status": "queued",
                "recipients": [{"email": "user@example.com", "status": "queued"}],
            },
        }

        with patch.object(
            client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.send_email(
                template_key="welcome-email",
                recipient=EmailRecipient(
                    email=" user@example.com ",
                    type="cc",
                    data={"locale": "en"},
                ),
                data={"first_name": "Ada"},
            )
            mock_request.assert_called_once_with(
                "/emails/send",
                method="POST",
                body={
                    "templateKey": "welcome-email",
                    "recipient": {
                        "email": "user@example.com",
                        "type": "cc",
                        "data": {"locale": "en"},
                    },
                    "data": {"first_name": "Ada"},
                },
            )

        await client.close()

    async def test_send_email_normalizes_recipient_type(self) -> None:
        client = HuefyEmailClient(api_key="sk_test_send_email")
        mock_response = {
            "success": True,
            "correlationId": "corr-123",
            "data": {
                "emailId": "email-1",
                "status": "queued",
                "recipients": [{"email": "user@example.com", "status": "queued"}],
            },
        }

        with patch.object(
            client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
        ) as mock_request:
            await client.send_email(
                template_key="welcome-email",
                recipient=EmailRecipient(
                    email=" user@example.com ",
                    type="CC",
                    data={"locale": "en"},
                ),
                data={"first_name": "Ada"},
            )
            mock_request.assert_called_once_with(
                "/emails/send",
                method="POST",
                body={
                    "templateKey": "welcome-email",
                    "recipient": {
                        "email": "user@example.com",
                        "type": "cc",
                        "data": {"locale": "en"},
                    },
                    "data": {"first_name": "Ada"},
                },
            )

        await client.close()
