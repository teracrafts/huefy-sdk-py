"""Data models for the Huefy SDK."""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .exceptions import ValidationError


class EmailProvider(str, Enum):
    """Enum representing supported email providers.

    This enum defines the email providers that can be used to send emails
    through the Huefy API. Each provider has its own capabilities and configuration.
    """

    SES = "ses"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    MAILCHIMP = "mailchimp"


class SendEmailRequest(BaseModel):
    """Request model for sending a single email.

    This class represents a request to send an email using a template.
    It includes the template key, recipient email address, template data,
    and optional provider specification.

    Attributes:
        template_key: The template key to use
        recipient: The recipient email address
        data: Template data for variable substitution
        provider: Optional email provider to use

    Example:
        >>> request = SendEmailRequest(
        ...     template_key="welcome-email",
        ...     recipient="john@example.com",
        ...     data={"name": "John Doe", "company": "Acme Corp"},
        ...     provider=EmailProvider.SENDGRID
        ... )
    """

    template_key: str = Field(..., description="The template key to use", alias="templateKey")
    recipient: str = Field(..., description="The recipient email address")
    data: Dict[str, Any] = Field(
        ..., description="Template data for variable substitution"
    )
    provider: Optional[EmailProvider] = Field(
        None, description="Optional email provider to use", alias="providerType"
    )

    @validator("template_key")
    def validate_template_key(cls, v: str) -> str:
        """Validate template key is not empty."""
        if not v or not v.strip():
            raise ValueError("Template key is required")
        return v.strip()

    @validator("recipient")
    def validate_recipient(cls, v: str) -> str:
        """Validate recipient email address."""
        if not v or not v.strip():
            raise ValueError("Recipient email is required")

        email = v.strip()
        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError(f"Invalid email address: {email}")

        return email

    @validator("data")
    def validate_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template data is not empty."""
        if not v:
            raise ValueError("Template data is required")
        return v

    def validate(self) -> None:
        """Validate the request.

        Raises:
            ValidationError: If the request is invalid
        """
        try:
            # Pydantic validation is called during model creation
            # This method is for explicit validation calls
            pass
        except ValueError as e:
            raise ValidationError(str(e))

    class Config:
        """Pydantic config."""

        use_enum_values = True
        validate_assignment = True
        allow_population_by_field_name = True


class SendEmailResponse(BaseModel):
    """Response model for email sending operations.

    This class represents the response from the Huefy API when an email
    is successfully sent. It contains information about the sent email including
    the message ID, status, provider used, and timestamp.

    Attributes:
        message_id: Unique message ID for the sent email
        status: Email status (e.g., "sent", "queued")
        provider: Email provider that was used
        timestamp: Timestamp when the email was sent
    """

    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Human-readable status message")
    message_id: str = Field(..., description="Unique message ID for the sent email", alias="messageId")
    provider: EmailProvider = Field(..., description="Email provider that was used")

    class Config:
        """Pydantic config."""

        use_enum_values = True
        allow_population_by_field_name = True


class BulkEmailResult(BaseModel):
    """Result of a single email in a bulk operation.

    Attributes:
        success: Whether the email was sent successfully
        result: Email response for successful sends
        error: Error information for failed sends
    """

    success: bool = Field(..., description="Whether the email was sent successfully")
    result: Optional[SendEmailResponse] = Field(
        None, description="Email response for successful sends"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, description="Error information for failed sends"
    )


class BulkEmailResponse(BaseModel):
    """Response model for bulk email operations.

    This class represents the response from the Huefy API when multiple emails
    are sent in a single bulk operation. It contains a list of results for each
    email that was processed.

    Attributes:
        results: List of results for each email
    """

    results: List[BulkEmailResult] = Field(
        ..., description="List of results for each email"
    )


class HealthResponse(BaseModel):
    """Response model for API health check operations.

    This class represents the response from the Huefy API health check endpoint.
    It provides information about the current status and health of the API service.

    Attributes:
        status: Health status of the API
        timestamp: Timestamp of the health check
        version: API version (optional)
    """

    status: str = Field(..., description="Health status of the API")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    version: Optional[str] = Field(None, description="API version")


class ErrorDetail(BaseModel):
    """Detailed information about an API error.

    Attributes:
        code: Error code
        message: Human-readable error message
        details: Additional error details
    """

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Response model for API error responses.

    This class represents an error response from the Huefy API.
    It contains detailed information about what went wrong.

    Attributes:
        error: Error detail information
    """

    error: ErrorDetail = Field(..., description="Error detail information")