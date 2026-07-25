"""Huefy SDK type definitions."""

from huefy.types.email import (
    EmailProvider,
    EmailRecipient,
    SendEmailRequest,
    SendEmailResponse,
    BulkRecipient,
    SendBulkEmailsRequest,
    SendBulkEmailsResponse,
    ValidateTemplateRequest,
    ValidateTemplateResponse,
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
    "ValidateTemplateRequest",
    "ValidateTemplateResponse",
    "BulkEmailResult",
    "HealthResponse",
]
