"""Tests for security utilities: PII detection and HMAC signing."""

from __future__ import annotations

import time

from huefy.utils.security import (
    create_request_signature,
    detect_potential_pii,
    generate_hmac_sha256,
    get_key_id,
    is_client_key,
    is_potential_pii_field,
    is_server_key,
    sign_payload,
    verify_request_signature,
    warn_if_potential_pii,
)
from huefy.utils.logger import NoopLogger


class TestPiiDetection:
    """Tests for PII field detection."""

    def test_detects_common_pii_fields(self) -> None:
        assert is_potential_pii_field("email") is True
        assert is_potential_pii_field("password") is True
        assert is_potential_pii_field("ssn") is True
        assert is_potential_pii_field("phone") is True
        assert is_potential_pii_field("first_name") is True
        assert is_potential_pii_field("credit_card") is True
        assert is_potential_pii_field("ip_address") is True

    def test_does_not_flag_safe_fields(self) -> None:
        assert is_potential_pii_field("template_id") is False
        assert is_potential_pii_field("subject") is False
        assert is_potential_pii_field("status") is False
        assert is_potential_pii_field("count") is False

    def test_case_insensitive(self) -> None:
        assert is_potential_pii_field("Email") is True
        assert is_potential_pii_field("PASSWORD") is True
        assert is_potential_pii_field("SSN") is True

    def test_detect_pii_in_flat_dict(self) -> None:
        data = {"email": "test@test.com", "template_id": "abc"}
        findings = detect_potential_pii(data)
        assert "email" in findings
        assert "template_id" not in findings

    def test_detect_pii_in_nested_dict(self) -> None:
        data = {
            "user": {
                "first_name": "John",
                "preferences": {"theme": "dark"},
            }
        }
        findings = detect_potential_pii(data)
        assert "user.first_name" in findings
        assert len(findings) == 1

    def test_detect_pii_in_list_of_dicts(self) -> None:
        data = {
            "contacts": [
                {"phone": "123-456-7890"},
                {"phone": "098-765-4321"},
            ]
        }
        findings = detect_potential_pii(data)
        assert "contacts[0].phone" in findings
        assert "contacts[1].phone" in findings

    def test_empty_data(self) -> None:
        assert detect_potential_pii({}) == []


class TestWarnIfPotentialPii:
    """Tests for the PII warning function."""

    def test_does_not_raise_with_noop_logger(self) -> None:
        logger = NoopLogger()
        data = {"email": "test@test.com"}
        # Should not raise
        warn_if_potential_pii(data, "test data", logger)

    def test_does_not_raise_with_no_logger(self) -> None:
        data = {"email": "test@test.com"}
        warn_if_potential_pii(data, "test data", None)


class TestHmacSigning:
    """Tests for HMAC-SHA256 signing."""

    def test_generate_hmac_sha256_deterministic(self) -> None:
        sig1 = generate_hmac_sha256("hello", "secret")
        sig2 = generate_hmac_sha256("hello", "secret")
        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex digest length

    def test_different_messages_produce_different_signatures(self) -> None:
        sig1 = generate_hmac_sha256("hello", "secret")
        sig2 = generate_hmac_sha256("world", "secret")
        assert sig1 != sig2

    def test_different_keys_produce_different_signatures(self) -> None:
        sig1 = generate_hmac_sha256("hello", "key1")
        sig2 = generate_hmac_sha256("hello", "key2")
        assert sig1 != sig2

    def test_sign_payload_returns_signature_and_timestamp(self) -> None:
        result = sign_payload({"key": "value"}, "api-key-123")
        assert "signature" in result
        assert "timestamp" in result
        assert len(result["signature"]) == 64

    def test_sign_payload_with_explicit_timestamp(self) -> None:
        result = sign_payload({"key": "value"}, "api-key-123", timestamp="1234567890")
        assert result["timestamp"] == "1234567890"

    def test_create_request_signature(self) -> None:
        result = create_request_signature({"foo": "bar"}, "my-api-key")
        assert "signature" in result
        assert "timestamp" in result


class TestVerifyRequestSignature:
    """Tests for signature verification."""

    def test_valid_signature_passes(self) -> None:
        body = {"action": "send", "to": "user@example.com"}
        api_key = "sk_test_verify_key_1234567890"

        signed = sign_payload(body, api_key)

        assert verify_request_signature(
            body=body,
            signature=signed["signature"],
            timestamp=signed["timestamp"],
            api_key=api_key,
        ) is True

    def test_tampered_body_fails(self) -> None:
        body = {"action": "send"}
        api_key = "sk_test_verify_key_1234567890"
        signed = sign_payload(body, api_key)

        tampered_body = {"action": "delete"}
        assert verify_request_signature(
            body=tampered_body,
            signature=signed["signature"],
            timestamp=signed["timestamp"],
            api_key=api_key,
        ) is False

    def test_wrong_key_fails(self) -> None:
        body = {"action": "send"}
        signed = sign_payload(body, "correct-key")

        assert verify_request_signature(
            body=body,
            signature=signed["signature"],
            timestamp=signed["timestamp"],
            api_key="wrong-key",
        ) is False

    def test_expired_timestamp_fails(self) -> None:
        body = {"action": "send"}
        api_key = "sk_test_key"
        old_ts = str(int(time.time() * 1000) - 400_000)  # 400s ago
        signed = sign_payload(body, api_key, timestamp=old_ts)

        assert verify_request_signature(
            body=body,
            signature=signed["signature"],
            timestamp=signed["timestamp"],
            api_key=api_key,
            max_age_ms=300_000,
        ) is False


class TestKeyUtilities:
    """Tests for key identification functions."""

    def test_get_key_id_returns_first_8_chars(self) -> None:
        assert get_key_id("sk_test_abcdefghijklmnop") == "sk_test_"

    def test_get_key_id_short_key(self) -> None:
        assert get_key_id("abc") == "abc"

    def test_is_server_key(self) -> None:
        assert is_server_key("sk_live_123456") is True
        assert is_server_key("sk-live-123456") is True
        assert is_server_key("pk_live_123456") is False

    def test_is_client_key(self) -> None:
        assert is_client_key("pk_live_123456") is True
        assert is_client_key("pk-live-123456") is True
        assert is_client_key("sk_live_123456") is False
