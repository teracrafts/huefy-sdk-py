"""Email validation utilities for the Huefy SDK."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from huefy.types.email import EmailRecipient

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MAX_EMAIL_LENGTH = 254
MAX_TEMPLATE_KEY_LENGTH = 100
MAX_BULK_EMAILS = 1000
VALID_RECIPIENT_TYPES = {"to", "cc", "bcc"}


def validate_email(email: str) -> Optional[str]:
    if not email or not isinstance(email, str):
        return "Recipient email is required"
    trimmed = email.strip()
    if len(trimmed) > MAX_EMAIL_LENGTH:
        return f"Email exceeds maximum length of {MAX_EMAIL_LENGTH} characters"
    if not EMAIL_REGEX.match(trimmed):
        return f"Invalid email address: {trimmed}"
    return None


def validate_template_key(template_key: str) -> Optional[str]:
    if not template_key or not isinstance(template_key, str):
        return "Template key is required"
    trimmed = template_key.strip()
    if len(trimmed) == 0:
        return "Template key cannot be empty"
    if len(trimmed) > MAX_TEMPLATE_KEY_LENGTH:
        return f"Template key exceeds maximum length of {MAX_TEMPLATE_KEY_LENGTH} characters"
    return None


def validate_email_data(data: Dict[str, Any]) -> Optional[str]:
    if data is None or not isinstance(data, dict):
        return "Template data must be a non-null dict"
    return None


def validate_bulk_count(count: int) -> Optional[str]:
    if count <= 0:
        return "At least one email is required"
    if count > MAX_BULK_EMAILS:
        return f"Maximum of {MAX_BULK_EMAILS} emails per bulk request"
    return None


def validate_recipient(recipient: Union[str, EmailRecipient]) -> Optional[str]:
    if isinstance(recipient, str):
        return validate_email(recipient)

    if not isinstance(recipient, EmailRecipient):
        return "Recipient must be an email string or EmailRecipient"

    email_err = validate_email(recipient.email)
    if email_err:
        return email_err

    normalized_type = recipient.type.strip().lower() if isinstance(recipient.type, str) else recipient.type
    if normalized_type is not None and normalized_type not in VALID_RECIPIENT_TYPES:
        return "Recipient type must be one of: to, cc, bcc"

    if recipient.data is not None and not isinstance(recipient.data, dict):
        return "Recipient data must be a dict when provided"

    return None


def validate_send_email_input(
    template_key: str, data: Dict[str, Any], recipient: Union[str, EmailRecipient]
) -> List[str]:
    errors: List[str] = []
    key_err = validate_template_key(template_key)
    if key_err:
        errors.append(key_err)
    data_err = validate_email_data(data)
    if data_err:
        errors.append(data_err)
    email_err = validate_recipient(recipient)
    if email_err:
        errors.append(email_err)
    return errors
