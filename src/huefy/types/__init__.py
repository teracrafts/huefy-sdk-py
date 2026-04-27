"""Huefy SDK type definitions."""

from huefy.types.email import (
    EmailProvider,
    EmailRecipient,
    SendEmailRequest,
    SendEmailResponse,
    BulkRecipient,
    SendBulkEmailsRequest,
    SendBulkEmailsResponse,
    BulkEmailResult,
    HealthResponse,
)

__all__ = [
    "EmailProvider",
    "EmailRecipient",
    "SendEmailRequest",
    "SendEmailResponse",
    "BulkRecipient",
    "SendBulkEmailsRequest",
    "SendBulkEmailsResponse",
    "BulkEmailResult",
    "HealthResponse",
]
