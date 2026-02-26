"""Security utilities: PII detection, HMAC signing, and key management."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from huefy.utils.logger import Logger


# ─── PII Detection ───────────────────────────────────────────────────────────

# Normalized PII patterns (lowercase, no hyphens/underscores). Field names are
# normalized the same way before substring matching, so these patterns match
# regardless of separator style (e.g. "date_of_birth", "dateOfBirth", "date-of-birth").
PII_PATTERNS: list[str] = [
    "email", "phone", "telephone", "mobile",
    "ssn", "socialsecurity",
    "creditcard", "cardnumber", "cvv",
    "password", "passwd", "secret", "token",
    "apikey", "privatekey",
    "accesstoken", "refreshtoken", "authtoken",
    "address", "street", "zipcode", "postalcode",
    "dateofbirth", "dob", "birthdate",
    "passport", "driverlicense", "nationalid",
    "bankaccount", "routingnumber", "iban", "swift",
]


def is_potential_pii_field(field_name: str) -> bool:
    """Check if a field name matches a known PII pattern.

    The field name is normalized by lowercasing and removing hyphens and
    underscores before checking for substring matches against PII patterns.

    Args:
        field_name: The field name to check.

    Returns:
        True if the normalized field name contains any PII pattern as a substring.
    """
    normalized = field_name.lower().replace("-", "").replace("_", "")
    return any(pattern in normalized for pattern in PII_PATTERNS)


def detect_potential_pii(
    data: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    """Recursively detect fields in a dictionary that may contain PII.

    Args:
        data: The dictionary to scan.
        prefix: Prefix for nested field paths (used in recursion).

    Returns:
        A list of dot-delimited field paths that match PII patterns.
    """
    findings: list[str] = []

    for key, value in data.items():
        full_path = f"{prefix}.{key}" if prefix else key

        if is_potential_pii_field(key):
            findings.append(full_path)

        if isinstance(value, dict):
            findings.extend(detect_potential_pii(value, prefix=full_path))
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    findings.extend(
                        detect_potential_pii(item, prefix=f"{full_path}[{idx}]")
                    )

    return findings


def warn_if_potential_pii(
    data: dict[str, Any],
    data_type: str,
    logger: Logger | None,
) -> None:
    """Log a warning if potential PII fields are detected.

    Args:
        data: The dictionary to scan.
        data_type: A label describing the data (e.g. "request body").
        logger: The logger to use for warnings.
    """
    if logger is None:
        return

    findings = detect_potential_pii(data)
    if findings:
        fields_str = ", ".join(findings)
        logger.warn(
            f"Potential PII detected in {data_type}: [{fields_str}]. "
            f"Ensure this data is handled according to your data protection policies."
        )


# ─── HMAC Signing ─────────────────────────────────────────────────────────────

def generate_hmac_sha256(message: str, key: str) -> str:
    """Generate an HMAC-SHA256 hex digest.

    Args:
        message: The message to sign.
        key: The signing key.

    Returns:
        The hex-encoded HMAC-SHA256 signature.
    """
    return hmac.new(
        key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def sign_payload(
    data: dict[str, Any],
    api_key: str,
    timestamp: str | None = None,
) -> dict[str, str]:
    """Sign a payload dictionary with HMAC-SHA256.

    The signing message is constructed as: ``{timestamp}.{json_body}``

    Args:
        data: The payload to sign.
        api_key: The API key used as the HMAC secret.
        timestamp: ISO timestamp override (defaults to current time in ms).

    Returns:
        A dict containing ``signature`` and ``timestamp``.
    """
    ts = timestamp or str(int(time.time() * 1000))
    body_str = json.dumps(data, separators=(",", ":"), sort_keys=True)
    message = f"{ts}.{body_str}"
    signature = generate_hmac_sha256(message, api_key)
    return {"signature": signature, "timestamp": ts}


def create_request_signature(
    body: dict[str, Any],
    api_key: str,
) -> dict[str, str]:
    """Create a full request signature for API authentication.

    Args:
        body: The request body to sign.
        api_key: The API key used for signing.

    Returns:
        A dict containing ``signature`` and ``timestamp``.
    """
    return sign_payload(body, api_key)


def verify_request_signature(
    body: dict[str, Any],
    signature: str,
    timestamp: str,
    api_key: str,
    max_age_ms: int = 300_000,
) -> bool:
    """Verify a request signature.

    Args:
        body: The request body that was signed.
        signature: The signature to verify.
        timestamp: The timestamp used during signing.
        api_key: The API key used for signing.
        max_age_ms: Maximum allowed age of the signature in milliseconds.

    Returns:
        True if the signature is valid and not expired.
    """
    # Check timestamp freshness
    try:
        ts_ms = int(timestamp)
    except (ValueError, TypeError):
        return False

    now_ms = int(time.time() * 1000)
    if abs(now_ms - ts_ms) > max_age_ms:
        return False

    # Recompute and compare
    expected = sign_payload(body, api_key, timestamp=timestamp)
    return hmac.compare_digest(expected["signature"], signature)


# ─── Key Utilities ────────────────────────────────────────────────────────────

def get_key_id(api_key: str) -> str:
    """Extract a non-sensitive key identifier from an API key.

    Returns the first 8 characters as an identifier suitable for logging
    and request headers.

    Args:
        api_key: The full API key.

    Returns:
        The first 8 characters of the key.
    """
    return api_key[:8] if len(api_key) >= 8 else api_key


def is_server_key(key: str) -> bool:
    """Check if an API key is a server-side key.

    Server keys start with ``srv_``.

    Args:
        key: The API key to check.

    Returns:
        True if the key appears to be a server key.
    """
    return key.lower().startswith("srv_")


def is_client_key(key: str) -> bool:
    """Check if an API key is a client-side key.

    Client keys start with ``sdk_`` or ``cli_``.

    Args:
        key: The API key to check.

    Returns:
        True if the key appears to be a client key.
    """
    lower = key.lower()
    return lower.startswith("sdk_") or lower.startswith("cli_")
