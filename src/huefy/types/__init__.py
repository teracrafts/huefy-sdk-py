"""Huefy SDK type definitions."""

from huefy.types.email import (
    EmailProvider,
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
    "SendEmailRequest",
    "SendEmailResponse",
    "BulkRecipient",
    "SendBulkEmailsRequest",
    "SendBulkEmailsResponse",
    "BulkEmailResult",
    "HealthResponse",
]
