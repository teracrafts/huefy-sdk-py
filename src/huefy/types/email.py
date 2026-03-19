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
class RecipientStatus:
    """Status of a single recipient in an email send."""
    email: str
    status: str
    messageId: Optional[str] = None
    error: Optional[str] = None
    sentAt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RecipientStatus:
        return cls(
            email=data.get("email", ""),
            status=data.get("status", ""),
            messageId=data.get("messageId"),
            error=data.get("error"),
            sentAt=data.get("sentAt"),
        )


@dataclass
class SendEmailResponseData:
    """Data payload from a send-email response."""
    emailId: str
    status: str
    recipients: List[RecipientStatus]
    scheduledAt: Optional[str] = None
    sentAt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendEmailResponseData:
        recipients = [RecipientStatus.from_dict(r) for r in data.get("recipients", [])]
        return cls(
            emailId=data.get("emailId", ""),
            status=data.get("status", ""),
            recipients=recipients,
            scheduledAt=data.get("scheduledAt"),
            sentAt=data.get("sentAt"),
        )


@dataclass
class SendEmailResponse:
    """Response from sending an email."""
    success: bool
    data: SendEmailResponseData
    correlationId: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendEmailResponse:
        return cls(
            success=data.get("success", False),
            data=SendEmailResponseData.from_dict(data.get("data", {})),
            correlationId=data.get("correlationId", ""),
        )


@dataclass
class BulkRecipient:
    """A single recipient in a bulk email send."""
    email: str
    type: str = "to"
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "email": self.email,
            "type": self.type,
        }
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class SendBulkEmailsRequest:
    """Request to send bulk emails via a template."""
    templateKey: str
    recipients: List[BulkRecipient]
    fromEmail: Optional[str] = None
    fromName: Optional[str] = None
    providerType: Optional[str] = None
    batchSize: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "templateKey": self.templateKey,
            "recipients": [r.to_dict() for r in self.recipients],
        }
        if self.fromEmail is not None:
            result["fromEmail"] = self.fromEmail
        if self.fromName is not None:
            result["fromName"] = self.fromName
        if self.providerType is not None:
            result["providerType"] = self.providerType
        if self.batchSize is not None:
            result["batchSize"] = self.batchSize
        if self.metadata is not None:
            result["metadata"] = self.metadata
        return result


@dataclass
class SendBulkEmailsResponseData:
    """Data payload from a send-bulk-emails response."""
    batchId: str
    status: str
    templateKey: str
    totalRecipients: int
    processedCount: int
    successCount: int
    failureCount: int
    suppressedCount: int
    startedAt: str
    recipients: List[RecipientStatus]
    completedAt: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendBulkEmailsResponseData:
        recipients = [RecipientStatus.from_dict(r) for r in data.get("recipients", [])]
        return cls(
            batchId=data.get("batchId", ""),
            status=data.get("status", ""),
            templateKey=data.get("templateKey", ""),
            totalRecipients=data.get("totalRecipients", 0),
            processedCount=data.get("processedCount", 0),
            successCount=data.get("successCount", 0),
            failureCount=data.get("failureCount", 0),
            suppressedCount=data.get("suppressedCount", 0),
            startedAt=data.get("startedAt", ""),
            recipients=recipients,
            completedAt=data.get("completedAt"),
            errors=data.get("errors"),
        )


@dataclass
class SendBulkEmailsResponse:
    """Response from sending bulk emails."""
    success: bool
    data: SendBulkEmailsResponseData
    correlationId: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendBulkEmailsResponse:
        return cls(
            success=data.get("success", False),
            data=SendBulkEmailsResponseData.from_dict(data.get("data", {})),
            correlationId=data.get("correlationId", ""),
        )


@dataclass
class HealthResponseData:
    """Data payload from a health check response."""
    status: str
    timestamp: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HealthResponseData:
        return cls(
            status=data.get("status", ""),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", ""),
        )


@dataclass
class HealthResponse:
    """Health check response."""
    success: bool
    data: HealthResponseData
    correlationId: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HealthResponse:
        return cls(
            success=data.get("success", False),
            data=HealthResponseData.from_dict(data.get("data", {})),
            correlationId=data.get("correlationId", ""),
        )
