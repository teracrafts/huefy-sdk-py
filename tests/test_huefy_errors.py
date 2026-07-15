import pytest
from huefy.errors.huefy_errors import (
    HuefyDomainError,
    AuthenticationError,
    TemplateNotFoundError,
    InvalidRecipientError,
    ProviderError,
    RateLimitError,
    InsufficientQuotaError,
    create_error_from_response,
)
from huefy.errors.error_codes import ErrorCode
from huefy.errors.huefy_error import HuefyError


class TestHuefyDomainErrors:
    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.code == "INVALID_API_KEY"
        assert err.status_code == 401

    def test_template_not_found(self):
        err = TemplateNotFoundError("welcome")
        assert "welcome" in str(err)
        assert err.status_code == 404

    def test_invalid_recipient(self):
        err = InvalidRecipientError("bad@")
        assert "bad@" in str(err)
        assert err.status_code == 400

    def test_rate_limit(self):
        err = RateLimitError("slow down", retry_after=30)
        assert err.retry_after == 30
        assert err.status_code == 429

    def test_insufficient_quota(self):
        err = InsufficientQuotaError("upgrade required")
        assert err.code == "INSUFFICIENT_QUOTA"
        assert err.status_code == 402

    def test_provider_error(self):
        err = ProviderError("SES failed", provider="ses")
        assert err.provider == "ses"

    def test_create_from_response(self):
        err = create_error_from_response({"error": "bad key", "code": "INVALID_API_KEY"}, 401)
        assert isinstance(err, AuthenticationError)

    def test_create_from_insufficient_quota(self):
        err = create_error_from_response(
            {"error": "quota exceeded", "code": "INSUFFICIENT_QUOTA"},
            402,
        )
        assert isinstance(err, InsufficientQuotaError)
        assert err.code == "INSUFFICIENT_QUOTA"
        assert err.status_code == 402

    def test_huefy_error_from_402_response(self):
        err = HuefyError.from_response(
            402,
            {
                "error": "quota exceeded",
                "code": "INSUFFICIENT_QUOTA",
                "requestId": "req_123",
                "details": {"limit": 1000, "used": 1000},
            },
        )
        assert err.code == ErrorCode.API_INSUFFICIENT_QUOTA
        assert err.status_code == 402
        assert err.recoverable is False
        assert err.request_id == "req_123"
        assert err.details["code"] == "INSUFFICIENT_QUOTA"

    def test_create_from_unknown(self):
        err = create_error_from_response({"error": "oops", "code": "WEIRD"}, 500)
        assert isinstance(err, HuefyDomainError)
        assert err.code == "WEIRD"
