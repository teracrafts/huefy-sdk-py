import pytest
from huefy.errors.huefy_errors import (
    HuefyDomainError,
    AuthenticationError,
    TemplateNotFoundError,
    InvalidRecipientError,
    ProviderError,
    RateLimitError,
    create_error_from_response,
)


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

    def test_provider_error(self):
        err = ProviderError("SES failed", provider="ses")
        assert err.provider == "ses"

    def test_create_from_response(self):
        err = create_error_from_response({"error": "bad key", "code": "INVALID_API_KEY"}, 401)
        assert isinstance(err, AuthenticationError)

    def test_create_from_unknown(self):
        err = create_error_from_response({"error": "oops", "code": "WEIRD"}, 500)
        assert isinstance(err, HuefyDomainError)
        assert err.code == "WEIRD"
