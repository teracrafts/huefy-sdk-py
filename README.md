# huefy

Official Python SDK for [Huefy](https://huefy.dev) — transactional email delivery made simple.

## Installation

```bash
pip install huefy
# or with uv
uv add huefy
# or with poetry
poetry add huefy
```

## Requirements

- Python 3.10+
- `httpx` (installed automatically)

## Quick Start

```python
import asyncio
from huefy import HuefyEmailClient, HuefyConfig

async def main():
    config = HuefyConfig(api_key="sdk_your_api_key")

    async with HuefyEmailClient(**config.to_kwargs()) as client:
        response = await client.send_email(
            template_key="welcome-email",
            recipient="alice@example.com",
            data={"first_name": "Alice", "trial_days": "14"},
        )
        print(response.data.emailId)

asyncio.run(main())
```

`recipient` can also be a structured object when you need recipient-specific template data or a non-default recipient type:

```python
from huefy import EmailRecipient

response = await client.send_email(
    template_key="welcome-email",
    recipient=EmailRecipient(
        email="reviewer@example.com",
        type="cc",
        data={"locale": "en"},
    ),
    data={"first_name": "Alice"},
)
```

## Key Features

- **Fully async** — built on `httpx` with `async`/`await` throughout
- **Async context manager** — `async with` ensures connections are closed cleanly
- **Retry with exponential backoff** — configurable attempts, base delay, ceiling, and jitter
- **Circuit breaker** — opens after 5 consecutive failures, probes after 30 s
- **HMAC-SHA256 signing** — optional request signing for additional integrity verification
- **Key rotation** — primary + secondary API key with seamless failover
- **Rate limit callbacks** — `on_rate_limit_update` fires whenever rate-limit headers change
- **PII detection** — warns when template variables contain sensitive field patterns
- **Error sanitization** — redacts file paths, IPs, keys, and emails from error messages
- **Pluggable logger** — supply any standard `logging.Logger` instance

## Configuration Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | `str` | — | **Required.** Must have prefix `sdk_`, `srv_`, or `cli_` |
| `base_url` | `str` | `https://api.huefy.dev/api/v1/sdk` | Override the API base URL |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `retry_config.max_attempts` | `int` | `3` | Total attempts including the first |
| `retry_config.base_delay` | `float` | `0.5` | Exponential backoff base delay (seconds) |
| `retry_config.max_delay` | `float` | `10.0` | Maximum backoff delay (seconds) |
| `retry_config.jitter` | `float` | `0.2` | Random jitter factor (0–1) |
| `circuit_breaker_config.failure_threshold` | `int` | `5` | Consecutive failures before circuit opens |
| `circuit_breaker_config.reset_timeout` | `float` | `30.0` | Seconds before half-open probe |
| `logger` | `Logger` | `None` | Standard `logging.Logger` instance |
| `secondary_api_key` | `str` | `None` | Backup key used during key rotation |
| `enable_request_signing` | `bool` | `False` | Enable HMAC-SHA256 request signing |
| `on_rate_limit_update` | `Callable` | `None` | Callback fired on rate-limit header changes |

## Bulk Email

```python
from huefy import BulkRecipient

bulk = await client.send_bulk_emails(
    template_key="promo",
    recipients=[
        BulkRecipient(email="bob@example.com"),
        BulkRecipient(email="carol@example.com"),
    ],
)

print(f"Sent: {bulk.data.successCount}, Failed: {bulk.data.failureCount}")
```

## Error Handling

```python
from huefy import (
    AuthenticationError,
    CircuitOpenError,
    HuefyEmailClient,
    HuefyConfig,
    HuefyError,
    RateLimitError,
)

async with HuefyEmailClient(**HuefyConfig(api_key="sdk_your_api_key").to_kwargs()) as client:
    try:
        response = await client.send_email(
            template_key="order-confirmation",
            recipient="user@example.com",
            data={},
        )
        print("Delivered:", response.data.emailId)
    except AuthenticationError:
        print("Invalid API key")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s")
    except CircuitOpenError:
        print("Circuit open — service unavailable, backing off")
    except HuefyError as e:
        print(f"Huefy error [{e.code}]: {e}")
```

### Error Code Reference

| Class | Code | Meaning |
|-------|------|---------|
| `AuthenticationError` | `INVALID_API_KEY` | API key rejected |
| `RateLimitError` | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `TemplateNotFoundError` | `TEMPLATE_NOT_FOUND` | Template key not found |
| `HuefyError` | `ErrorCode.*` | Transport or HTTP-layer SDK failure |

## Health Check

```python
health = await client.health_check()
if health["data"]["status"] != "healthy":
    print("Huefy degraded:", health["data"]["status"])
```

## Local Development

`HUEFY_MODE=local` resolves to `https://api.huefy.on/api/v1/sdk`. To bypass Caddy and hit the raw app port directly, override `base_url` to `http://localhost:8080/api/v1/sdk`:

```python
from huefy import HuefyEmailClient, HuefyConfig

config = HuefyConfig(
    api_key="sdk_local_key",
    base_url="https://api.huefy.on/api/v1/sdk",
)

client = HuefyEmailClient(**config.to_kwargs())
```

## Developer Guide

Full documentation, advanced patterns, and provider configuration are in the [Python Developer Guide](../../docs/spec/guides/python.guide.md).

## License

MIT
