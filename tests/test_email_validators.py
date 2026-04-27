import pytest
from huefy.types import EmailRecipient
from huefy.validators.email_validators import (
    validate_email,
    validate_template_key,
    validate_email_data,
    validate_bulk_count,
    validate_recipient,
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
        assert validate_email_data({"count": 5}) is None


class TestValidateBulkCount:
    def test_valid_count(self):
        assert validate_bulk_count(10) is None

    def test_zero(self):
        assert validate_bulk_count(0) is not None

    def test_over_limit(self):
        assert validate_bulk_count(1001) is not None


class TestValidateSendEmailInput:
    def test_valid_input(self):
        assert validate_send_email_input("tpl", {"name": "John"}, "user@test.com") == []

    def test_valid_recipient_object(self):
        assert validate_send_email_input(
            "tpl",
            {"name": "John"},
            EmailRecipient(email="user@test.com", type="cc", data={"segment": "vip"}),
        ) == []

    def test_invalid_input(self):
        errors = validate_send_email_input("", {}, "bad")
        assert len(errors) > 0


class TestValidateRecipient:
    def test_invalid_recipient_type(self):
        assert validate_recipient(
            EmailRecipient(email="user@test.com", type="weird"),
        ) is not None

    def test_invalid_recipient_data(self):
        assert validate_recipient(
            EmailRecipient(email="user@test.com", data=[]),  # type: ignore[arg-type]
        ) is not None

    def test_recipient_type_is_case_insensitive(self):
        assert validate_recipient(
            EmailRecipient(email="user@test.com", type="CC"),
        ) is None
