"""Huefy email client extending the base SDK client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from .client import HuefyClient as BaseClient
from .types.email import (
    EmailProvider,
    EmailRecipient,
    SendEmailRequest,
    SendEmailResponse,
    BulkRecipient,
    SendBulkEmailsRequest,
    SendBulkEmailsResponse,
    HealthResponse,
)
from .validators.email_validators import (
    validate_send_email_input,
    validate_bulk_count,
    validate_bulk_recipient,
    validate_template_key,
)
from .errors.huefy_errors import HuefyDomainError
from .utils.security import warn_if_potential_pii


class HuefyEmailClient(BaseClient):
    """Email client for the Huefy platform."""

    async def send_email(
        self,
        *,
        template_key: str,
        data: Dict[str, Any],
        recipient: Union[str, EmailRecipient],
        provider: Optional[EmailProvider] = None,
    ) -> SendEmailResponse:
        errors = validate_send_email_input(template_key, data, recipient)
        if errors:
            raise HuefyDomainError(
                "; ".join(errors),
                "VALIDATION_ERROR",
                400,
                {"validation_errors": errors},
            )

        if provider is not None and not isinstance(provider, EmailProvider):  # type: ignore[unreachable]
            valid_values = ", ".join(p.value for p in EmailProvider)
            raise HuefyDomainError(
                f"Invalid provider: {provider!r}. Must be an EmailProvider enum value ({valid_values})",
                "VALIDATION_ERROR",
                400,
                {"valid_providers": [p.value for p in EmailProvider]},
            )

        warn_if_potential_pii(data, "template data", self._logger)

        normalized_recipient = _normalize_recipient(recipient)
        if isinstance(normalized_recipient, EmailRecipient) and normalized_recipient.data:
            warn_if_potential_pii(normalized_recipient.data, "recipient template data", self._logger)

        request = SendEmailRequest(
            template_key=template_key.strip(),
            recipient=normalized_recipient,
            data=data,
            provider=provider,
        )
        response = await self._http_client.request(
            "/emails/send", method="POST", body=request.to_dict()
        )
        return SendEmailResponse.from_dict(response)

    async def send_bulk_emails(
        self,
        *,
        template_key: str,
        recipients: List[BulkRecipient],
        provider: Optional[EmailProvider] = None,
    ) -> SendBulkEmailsResponse:
        count_err = validate_bulk_count(len(recipients))
        if count_err:
            raise HuefyDomainError(count_err, "VALIDATION_ERROR", 400)

        template_err = validate_template_key(template_key)
        if template_err:
            raise HuefyDomainError(template_err, "VALIDATION_ERROR", 400)

        normalized_recipients: List[BulkRecipient] = []
        for i, recipient in enumerate(recipients):
            recipient_err = validate_bulk_recipient(
                EmailRecipient(
                    email=recipient.email,
                    type=recipient.type,
                    data=recipient.data,
                )
            )
            if recipient_err:
                raise HuefyDomainError(
                    f"recipients[{i}]: {recipient_err}",
                    "VALIDATION_ERROR",
                    400,
                )
            normalized_recipients.append(
                BulkRecipient(
                    email=recipient.email.strip(),
                    type=recipient.type.strip().lower(),
                    data=recipient.data,
                )
            )

        request = SendBulkEmailsRequest(
            templateKey=template_key.strip(),
            recipients=normalized_recipients,
            providerType=provider.value if provider is not None else None,
        )

        response = await self._http_client.request(
            "/emails/send-bulk", method="POST", body=request.to_dict()
        )
        return SendBulkEmailsResponse.from_dict(response)

    async def email_health_check(self) -> HealthResponse:
        response = await self._http_client.request("/health", method="GET")
        return HealthResponse.from_dict(response)


def _normalize_recipient(recipient: Union[str, EmailRecipient]) -> Union[str, EmailRecipient]:
    if isinstance(recipient, str):
        return recipient.strip()

    return EmailRecipient(
        email=recipient.email.strip(),
        type=recipient.type.strip().lower() if isinstance(recipient.type, str) else recipient.type,
        data=recipient.data,
    )
