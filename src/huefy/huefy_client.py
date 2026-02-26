"""Huefy email client extending the base SDK client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HuefyClient as BaseClient
from .types.email import (
    EmailProvider,
    SendEmailRequest,
    SendEmailResponse,
    BulkEmailResult,
    HealthResponse,
)
from .validators.email_validators import (
    validate_send_email_input,
    validate_bulk_count,
)
from .errors.huefy_errors import HuefyDomainError
from .utils.security import warn_if_potential_pii


class HuefyEmailClient(BaseClient):
    """Email client for the Huefy platform."""

    async def send_email(
        self,
        template_key: str,
        data: Dict[str, str],
        recipient: str,
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

        request = SendEmailRequest(
            template_key=template_key.strip(),
            recipient=recipient.strip(),
            data=data,
            provider=provider,
        )
        response = await self._http_client.request(
            "/emails/send", method="POST", body=request.to_dict()
        )
        return SendEmailResponse.from_dict(response)

    async def send_bulk_emails(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[BulkEmailResult]:
        count_err = validate_bulk_count(len(emails))
        if count_err:
            raise HuefyDomainError(count_err, "VALIDATION_ERROR", 400)

        requests = []
        for email in emails:
            errors = validate_send_email_input(
                email.get("template_key", ""),
                email.get("data", {}),
                email.get("recipient", ""),
            )
            if errors:
                raise HuefyDomainError(
                    f"Validation failed for {email.get('recipient', 'unknown')}: {'; '.join(errors)}",
                    "VALIDATION_ERROR",
                    400,
                    {"validation_errors": errors},
                )
            bulk_provider = email.get("provider")
            if bulk_provider is not None and not isinstance(bulk_provider, EmailProvider):  # type: ignore[unreachable]
                valid_values = ", ".join(p.value for p in EmailProvider)
                raise HuefyDomainError(
                    f"Invalid provider for {email.get('recipient', 'unknown')}: {bulk_provider!r}. "
                    f"Must be an EmailProvider enum value ({valid_values})",
                    "VALIDATION_ERROR",
                    400,
                    {"valid_providers": [p.value for p in EmailProvider]},
                )
            req = SendEmailRequest(
                template_key=email["template_key"].strip(),
                recipient=email["recipient"].strip(),
                data=email["data"],
                provider=bulk_provider,
            )
            requests.append(req.to_dict())

        response = await self._http_client.request(
            "/emails/bulk", method="POST", body={"emails": requests}
        )
        return [BulkEmailResult.from_dict(r) for r in response.get("results", [])]

    async def email_health_check(self) -> HealthResponse:
        response = await self._http_client.request("/health", method="GET")
        return HealthResponse.from_dict(response)
