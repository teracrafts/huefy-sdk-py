import pytest
from huefy.validators.email_validators import (
    validate_email,
    validate_template_key,
    validate_email_data,
    validate_bulk_count,
    validate_send_email_input,
)


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") is None

    def test_empty_email(self):
        assert validate_email("") is not None

    def test_invalid_email(self):
        assert validate_email("not-an-email") is not None

    def test_long_email(self):
        assert validate_email("a" * 250 + "@b.co") is not None


class TestValidateTemplateKey:
    def test_valid_key(self):
        assert validate_template_key("welcome-email") is None

    def test_empty_key(self):
        assert validate_template_key("") is not None

    def test_long_key(self):
        assert validate_template_key("a" * 101) is not None


class TestValidateEmailData:
    def test_valid_data(self):
        assert validate_email_data({"name": "John"}) is None

    def test_none(self):
        assert validate_email_data(None) is not None

    def test_non_string_value(self):
        assert validate_email_data({"count": 5}) is not None


class TestValidateBulkCount:
    def test_valid_count(self):
        assert validate_bulk_count(10) is None

    def test_zero(self):
        assert validate_bulk_count(0) is not None

    def test_over_limit(self):
        assert validate_bulk_count(101) is not None


class TestValidateSendEmailInput:
    def test_valid_input(self):
        assert validate_send_email_input("tpl", {"name": "John"}, "user@test.com") == []

    def test_invalid_input(self):
        errors = validate_send_email_input("", {}, "bad")
        assert len(errors) > 0
