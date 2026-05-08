"""
Huefy Python SDK Lab
Core email contract verification with optional live sends.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from huefy import HuefyEmailClient  # noqa: E402
from huefy.errors.huefy_errors import HuefyDomainError  # noqa: E402
from huefy.types.email import (  # noqa: E402
    BulkRecipient,
    EmailProvider,
    EmailRecipient,
    SendBulkEmailsResponse,
    SendEmailResponse,
)

PASS = "\033[32m[PASS]\033[0m"
FAIL = "\033[31m[FAIL]\033[0m"
LIVE_MODE = os.getenv("HUEFY_SDK_LAB_MODE", "").strip().lower() == "live"
VALID_PROVIDERS = {provider.value: provider for provider in EmailProvider}

passed = 0
failed = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        print(f"{PASS} {label}")
        passed += 1
    else:
        print(f"{FAIL} {label}" + (f" — {detail}" if detail else ""))
        failed += 1


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required in live mode")
    return value


def resolve_provider() -> Optional[EmailProvider]:
    value = os.getenv("HUEFY_SDK_LIVE_PROVIDER", "").strip().lower()
    if not value:
        return None
    provider = VALID_PROVIDERS.get(value)
    if provider is None:
        valid = ", ".join(sorted(VALID_PROVIDERS))
        raise ValueError(f"HUEFY_SDK_LIVE_PROVIDER must be one of: {valid}")
    return provider


def get_live_config() -> dict[str, object]:
    return {
        "api_key": require_env("HUEFY_SDK_LIVE_API_KEY"),
        "base_url": require_env("HUEFY_SDK_LIVE_BASE_URL"),
        "template_key": require_env("HUEFY_SDK_LIVE_TEMPLATE_KEY"),
        "recipient": require_env("HUEFY_SDK_LIVE_RECIPIENT"),
        "provider": resolve_provider(),
    }


class StubHttpClient:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    async def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        self.calls.append((path, method, body))
        if not self.responses:
            raise AssertionError("StubHttpClient exhausted")
        return self.responses.pop(0)

    async def close(self) -> None:
        return None


async def run_contract() -> None:
    client: HuefyEmailClient | None = None
    try:
        client = HuefyEmailClient(api_key="sdk_lab_test_key")
        check("Initialization", True)
    except Exception as e:
        check("Initialization", False, str(e))

    try:
        email_client = HuefyEmailClient(api_key="sdk_lab_test_key")
        stub = StubHttpClient(
            [
                {
                    "success": True,
                    "data": {
                        "emailId": "email_123",
                        "status": "queued",
                        "recipients": [{"email": "alice@example.com", "status": "queued"}],
                    },
                    "correlationId": "corr_send_123",
                }
            ]
        )
        email_client._http_client = stub  # type: ignore[attr-defined]
        response = await email_client.send_email(
            template_key=" welcome-email ",
            data={"firstName": "Alice"},
            recipient=EmailRecipient(email=" alice@example.com ", type="CC", data={"locale": "en"}),
            provider=EmailProvider.SES,
        )
        path, method, body = stub.calls[0]
        recipient = body["recipient"] if body else None
        ok = (
            path == "/emails/send"
            and method == "POST"
            and isinstance(body, dict)
            and body["templateKey"] == "welcome-email"
            and isinstance(recipient, dict)
            and recipient["email"] == "alice@example.com"
            and recipient["type"] == "cc"
            and body["providerType"] == "ses"
            and isinstance(response, SendEmailResponse)
            and response.data.emailId == "email_123"
        )
        check("Single email contract", ok, "" if ok else str(stub.calls))
    except Exception as e:
        check("Single email contract", False, str(e))

    try:
        email_client = HuefyEmailClient(api_key="sdk_lab_test_key")
        stub = StubHttpClient(
            [
                {
                    "success": True,
                    "data": {
                        "batchId": "batch_123",
                        "status": "processing",
                        "templateKey": "digest",
                        "totalRecipients": 2,
                        "processedCount": 0,
                        "successCount": 0,
                        "failureCount": 0,
                        "suppressedCount": 0,
                        "startedAt": "2026-05-07T10:00:00Z",
                        "recipients": [
                            {"email": "alice@example.com", "status": "queued"},
                            {"email": "bob@example.com", "status": "queued"},
                        ],
                    },
                    "correlationId": "corr_bulk_123",
                }
            ]
        )
        email_client._http_client = stub  # type: ignore[attr-defined]
        response = await email_client.send_bulk_emails(
            template_key=" digest ",
            recipients=[
                BulkRecipient(email=" alice@example.com ", type="TO", data={"locale": "en"}),
                BulkRecipient(email=" bob@example.com ", type="BCC"),
            ],
            provider=EmailProvider.MAILGUN,
        )
        path, method, body = stub.calls[0]
        recipients = body["recipients"] if body else None
        ok = (
            path == "/emails/send-bulk"
            and method == "POST"
            and isinstance(body, dict)
            and body["templateKey"] == "digest"
            and body["providerType"] == "mailgun"
            and isinstance(recipients, list)
            and recipients[0]["email"] == "alice@example.com"
            and recipients[0]["type"] == "to"
            and recipients[1]["type"] == "bcc"
            and isinstance(response, SendBulkEmailsResponse)
            and response.data.batchId == "batch_123"
        )
        check("Bulk email contract", ok, "" if ok else str(stub.calls))
    except Exception as e:
        check("Bulk email contract", False, str(e))

    try:
        email_client = HuefyEmailClient(api_key="sdk_lab_test_key")
        email_client._http_client = StubHttpClient([{}])  # type: ignore[attr-defined]
        await email_client.send_email(
            template_key="welcome",
            data={},
            recipient=EmailRecipient(email="not-an-email", type="reply-to"),
        )
        check("Validation rejects invalid single recipient", False, "expected validation error")
    except HuefyDomainError as e:
        check(
            "Validation rejects invalid single recipient",
            "invalid email" in str(e).lower() or "recipient type" in str(e).lower(),
            str(e),
        )
    except Exception as e:
        check("Validation rejects invalid single recipient", False, str(e))

    try:
        email_client = HuefyEmailClient(api_key="sdk_lab_test_key")
        email_client._http_client = StubHttpClient([{}])  # type: ignore[attr-defined]
        await email_client.send_bulk_emails(template_key="digest", recipients=[])
        check("Validation rejects invalid bulk request", False, "expected validation error")
    except HuefyDomainError as e:
        check("Validation rejects invalid bulk request", "at least one email" in str(e).lower(), str(e))
    except Exception as e:
        check("Validation rejects invalid bulk request", False, str(e))

    try:
        health_client = HuefyEmailClient(api_key="sdk_lab_test_key")
        stub = StubHttpClient(
            [
                {
                    "success": True,
                    "data": {
                        "status": "healthy",
                        "timestamp": "2026-05-07T10:00:00Z",
                        "version": "1.0.0",
                    },
                    "correlationId": "corr_health_123",
                }
            ]
        )
        health_client._http_client = stub  # type: ignore[attr-defined]
        response = await health_client.email_health_check()
        path, method, _ = stub.calls[0]
        ok = path == "/health" and method == "GET" and response.data.status == "healthy"
        check("Health check path", ok, "" if ok else str(stub.calls))
    except Exception as e:
        check("Health check path", False, str(e))

    try:
        if client is not None:
            await client.close()
        check("Cleanup", True)
    except Exception as e:
        check("Cleanup", False, str(e))


async def run_live() -> None:
    live = get_live_config()
    client: HuefyEmailClient | None = None

    try:
        client = HuefyEmailClient(
            api_key=str(live["api_key"]),
            base_url=str(live["base_url"]),
        )
        check("Initialization", True)
    except Exception as e:
        check("Initialization", False, str(e))
        return

    try:
        response = await client.email_health_check()
        ok = response.success and response.data.status == "healthy"
        check("Health check", ok, "" if ok else str(response))
    except Exception as e:
        check("Health check", False, str(e))

    provider = live["provider"]

    try:
        response = await client.send_email(
            template_key=str(live["template_key"]),
            data={"sdkLabMode": "live", "sdk": "python", "operation": "single"},
            recipient=str(live["recipient"]),
            provider=provider if isinstance(provider, EmailProvider) else None,
        )
        ok = response.success and bool(response.data.emailId)
        check("Single send", ok, "" if ok else str(response))
    except Exception as e:
        check("Single send", False, str(e))

    try:
        response = await client.send_bulk_emails(
            template_key=str(live["template_key"]),
            recipients=[
                BulkRecipient(
                    email=str(live["recipient"]),
                    type="to",
                    data={"sdkLabMode": "live", "sdk": "python", "operation": "bulk"},
                )
            ],
            provider=provider if isinstance(provider, EmailProvider) else None,
        )
        ok = response.success and bool(response.data.batchId) and response.data.totalRecipients >= 1
        check("Bulk send", ok, "" if ok else str(response))
    except Exception as e:
        check("Bulk send", False, str(e))

    try:
        await client.send_email(
            template_key=str(live["template_key"]),
            data={"sdkLabMode": "live", "sdk": "python", "operation": "invalid-single"},
            recipient="not-an-email",
            provider=provider if isinstance(provider, EmailProvider) else None,
        )
        check("Invalid single rejection", False, "expected validation error")
    except HuefyDomainError as e:
        check("Invalid single rejection", "invalid email" in str(e).lower(), str(e))
    except Exception as e:
        check("Invalid single rejection", False, str(e))

    try:
        await client.send_bulk_emails(
            template_key=str(live["template_key"]),
            recipients=[],
            provider=provider if isinstance(provider, EmailProvider) else None,
        )
        check("Invalid bulk rejection", False, "expected validation error")
    except HuefyDomainError as e:
        check("Invalid bulk rejection", "at least one email" in str(e).lower(), str(e))
    except Exception as e:
        check("Invalid bulk rejection", False, str(e))

    try:
        await client.close()
        check("Cleanup", True)
    except Exception as e:
        check("Cleanup", False, str(e))


async def run() -> None:
    print("=== Huefy Python SDK Lab ===\n")
    print(f"Mode: {'live' if LIVE_MODE else 'contract'}\n")

    if LIVE_MODE:
        await run_live()
    else:
        await run_contract()

    print("\n========================================")
    print(f"Results: {passed} passed, {failed} failed")
    print("========================================\n")

    if failed == 0:
        print("All verifications passed!")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())
