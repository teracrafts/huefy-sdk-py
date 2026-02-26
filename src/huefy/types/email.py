"""Email-specific types for the Huefy SDK."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EmailProvider(str, Enum):
    """Supported email providers."""
    SES = "ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    MAILCHIMP = "mailchimp"


@dataclass
class SendEmailRequest:
    """Request to send a single email."""
    template_key: str
    recipient: str
    data: Dict[str, str]
    provider: Optional[EmailProvider] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "templateKey": self.template_key,
            "recipient": self.recipient,
            "data": self.data,
        }
        if self.provider is not None:
            result["providerType"] = self.provider.value
        return result


@dataclass
class SendEmailResponse:
    """Response from sending an email."""
    success: bool
    message: str
    message_id: str
    provider: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendEmailResponse:
        return cls(
            success=data.get("success", False),
            message=data.get("message", ""),
            message_id=data.get("messageId", ""),
            provider=data.get("provider", ""),
        )


@dataclass
class BulkEmailResult:
    """Result of a single email in a bulk send."""
    email: str
    success: bool
    result: Optional[SendEmailResponse] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BulkEmailResult:
        result = None
        if data.get("result"):
            result = SendEmailResponse.from_dict(data["result"])
        return cls(
            email=data.get("email", ""),
            success=data.get("success", False),
            result=result,
            error=data.get("error"),
        )


@dataclass
class HealthResponse:
    """Health check response."""
    status: str
    timestamp: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HealthResponse:
        return cls(
            status=data.get("status", ""),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", ""),
        )
