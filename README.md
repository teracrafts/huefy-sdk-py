# huefy

Official Python SDK for [Huefy](https://huefy.dev) — transactional email delivery made simple.

## Installation

```bash
pip install huefy-sdk
# or with uv
uv add huefy-sdk
# or with poetry
poetry add huefy-sdk
```

## Requirements

- Python 3.10+
- `httpx` (installed automatically)

## Quick Start

```python
import asyncio
from huefy import HuefyEmailClient, HuefyConfig

async def main():
    async with HuefyEmailClient(HuefyConfig(api_key="sdk_your_api_key")) as client:
        response = await client.send_email({
            "template_key": "welcome-email",
            "recipient": {"email": "alice@example.com", "name": "Alice"},
            "variables": {"first_name": "Alice", "trial_days": 14},
        })
        print(response.message_id)

asyncio.run(main())
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
bulk = await client.send_bulk_emails({
    "emails": [
        {"template_key": "promo", "recipient": {"email": "bob@example.com"}},
        {"template_key": "promo", "recipient": {"email": "carol@example.com"}},
    ]
})

print(f"Sent: {bulk.total_sent}, Failed: {bulk.total_failed}")
```

## Error Handling

```python
from huefy import (
    HuefyEmailClient,
    HuefyConfig,
    HuefyError,
    HuefyAuthError,
    HuefyRateLimitError,
    HuefyCircuitOpenError,
    HuefyNetworkError,
)

async with HuefyEmailClient(HuefyConfig(api_key="sdk_your_api_key")) as client:
    try:
        response = await client.send_email({
            "template_key": "order-confirmation",
            "recipient": {"email": "user@example.com"},
        })
        print("Delivered:", response.message_id)
    except HuefyAuthError:
        print("Invalid API key")
    except HuefyRateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s")
    except HuefyCircuitOpenError:
        print("Circuit open — service unavailable, backing off")
    except HuefyNetworkError as e:
        print("Network error:", e)
    except HuefyError as e:
        print(f"Huefy error [{e.code}]: {e}")
```

### Error Code Reference

| Class | Code | Meaning |
|-------|------|---------|
| `HuefyInitError` | 1001 | Client failed to initialise |
| `HuefyAuthError` | 1102 | API key rejected |
| `HuefyNetworkError` | 1201 | Upstream request failed |
| `HuefyCircuitOpenError` | 1301 | Circuit breaker tripped |
| `HuefyRateLimitError` | 2003 | Rate limit exceeded |
| `HuefyTemplateMissingError` | 2005 | Template key not found |

## Health Check

```python
health = await client.health_check()
if health.status != "healthy":
    print("Huefy degraded:", health.status)
```

## Local Development

Set `HUEFY_MODE=local` to point the SDK at a local Huefy server, or override `base_url` directly:

```python
from huefy import HuefyEmailClient, HuefyConfig

client = HuefyEmailClient(HuefyConfig(
    api_key="sdk_local_key",
    base_url="http://localhost:3000/api/v1/sdk",
))
```

## Developer Guide

Full documentation, advanced patterns, and provider configuration are in the [Python Developer Guide](../../docs/spec/guides/python.guide.md).

## License

MIT
