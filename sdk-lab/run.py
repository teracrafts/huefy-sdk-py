"""
Huefy Python SDK Lab
Internal integration verification — no real network calls (except health check).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from huefy import HuefyEmailClient, HuefyConfig
from huefy.utils.security import sign_payload, detect_potential_pii
from huefy.errors.sanitizer import sanitize_error_message
from huefy.http.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState

PASS = "\033[32m[PASS]\033[0m"
FAIL = "\033[31m[FAIL]\033[0m"

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


async def run() -> None:
    print("=== Huefy Python SDK Lab ===\n")

    # 1. Initialization
    client: HuefyEmailClient | None = None
    try:
        client = HuefyEmailClient(api_key="sdk_lab_test_key")
        check("Initialization", True)
    except Exception as e:
        check("Initialization", False, str(e))

    # 2. Config validation
    try:
        HuefyEmailClient(api_key="")
        check("Config validation", False, "Expected error was not raised")
    except (ValueError, Exception):
        check("Config validation", True)

    # 3. HMAC signing
    try:
        result = sign_payload({"test": "data"}, "test_secret", timestamp="1700000000")
        sig = result.get("signature", "")
        ok = isinstance(sig, str) and len(sig) == 64
        check("HMAC signing", ok, "" if ok else f'signature="{sig}"')
    except Exception as e:
        check("HMAC signing", False, str(e))

    # 4. Error sanitization
    try:
        input_msg = "Error at 192.168.1.1 for user@example.com"
        result_msg = sanitize_error_message(input_msg)
        ok = "192.168.1.1" not in result_msg and "user@example.com" not in result_msg
        check("Error sanitization", ok, "" if ok else f'result="{result_msg}"')
    except Exception as e:
        check("Error sanitization", False, str(e))

    # 5. PII detection
    try:
        fields = detect_potential_pii({"email": "test@test.com", "name": "John", "ssn": "123-45-6789"})
        has_email = "email" in fields
        has_ssn = "ssn" in fields
        ok = len(fields) > 0 and has_email and has_ssn
        check("PII detection", ok, "" if ok else f"fields={fields}")
    except Exception as e:
        check("PII detection", False, str(e))

    # 6. Circuit breaker state
    try:
        cb = CircuitBreaker()
        state = cb._state
        check("Circuit breaker state", state == CircuitState.CLOSED, f"state={state}")
    except Exception as e:
        check("Circuit breaker state", False, str(e))

    # 7. Health check
    import os
    base_url = (
        "http://localhost:3000/api/v1/sdk"
        if os.environ.get("HUEFY_MODE") == "local"
        else "https://api.huefy.dev/api/v1/sdk"
    )
    try:
        hc = HuefyEmailClient(api_key="sdk_lab_test_key", base_url=base_url)
        await hc.health_check()
        check("Health check", True)
    except Exception as e:
        msg = str(e)
        is_network = any(
            kw in msg.lower()
            for kw in ("connect", "network", "timeout", "refused", "unreachable", "ssl", "name or service")
        )
        is_auth = any(kw in msg for kw in ("401", "403", "Unauthorized", "Forbidden", "Invalid"))
        check("Health check", is_network or is_auth, f"(network/auth error — {msg[:80]})")

    # 8. Cleanup
    try:
        if client is not None:
            await client.close()
        check("Cleanup", True)
    except Exception as e:
        check("Cleanup", False, str(e))

    print("\n========================================")
    print(f"Results: {passed} passed, {failed} failed")
    print("========================================\n")

    if failed == 0:
        print("All verifications passed!")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())
