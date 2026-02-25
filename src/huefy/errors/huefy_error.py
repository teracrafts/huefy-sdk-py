"""Custom exception class for Huefy SDK errors."""

from __future__ import annotations

import time
from typing import Any

from huefy.errors.error_codes import ErrorCode, NUMERIC_CODE_MAP, is_recoverable_code


class HuefyError(Exception):
    """Base exception for all Huefy SDK errors.

    Provides structured error information including error codes, HTTP status,
    recoverability, and request tracing metadata.
    """

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode = ErrorCode.UNKNOWN,
        status_code: int | None = None,
        recoverable: bool = False,
        retry_after: float | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.numeric_code = NUMERIC_CODE_MAP.get(code, 9000)
        self.status_code = status_code
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.request_id = request_id
        self.timestamp = time.time()
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error to a dictionary."""
        return {
            "message": str(self),
            "code": self.code.value,
            "numeric_code": self.numeric_code,
            "status_code": self.status_code,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def network_error(
        cls,
        message: str = "A network error occurred",
        url: str | None = None,
    ) -> HuefyError:
        """Create a network error.

        Args:
            message: Error description.
            url: The URL that was being requested.

        Returns:
            A HuefyError configured as a network error.
        """
        details: dict[str, Any] = {}
        if url:
            details["url"] = url

        return cls(
            message=message,
            code=ErrorCode.NETWORK_ERROR,
            recoverable=True,
            details=details,
        )

    @classmethod
    def authentication_error(
        cls,
        message: str = "Authentication failed",
        code: ErrorCode = ErrorCode.AUTH_INVALID_KEY,
    ) -> HuefyError:
        """Create an authentication error.

        Args:
            message: Error description.
            code: Specific auth error code.

        Returns:
            A HuefyError configured as an authentication error.
        """
        return cls(
            message=message,
            code=code,
            status_code=401,
            recoverable=False,
        )

    @classmethod
    def timeout_error(
        cls,
        url: str | None = None,
        timeout: float | None = None,
    ) -> HuefyError:
        """Create a timeout error.

        Args:
            url: The URL that timed out.
            timeout: The timeout value in seconds.

        Returns:
            A HuefyError configured as a timeout error.
        """
        parts = ["Request timed out"]
        if timeout is not None:
            parts.append(f"after {timeout}s")
        if url:
            parts.append(f"for {url}")

        details: dict[str, Any] = {}
        if url:
            details["url"] = url
        if timeout is not None:
            details["timeout"] = timeout

        return cls(
            message=" ".join(parts),
            code=ErrorCode.NETWORK_TIMEOUT,
            recoverable=True,
            details=details,
        )

    @classmethod
    def from_response(
        cls,
        status_code: int,
        body: dict[str, Any] | None = None,
    ) -> HuefyError:
        """Create an error from an HTTP response.

        Args:
            status_code: The HTTP status code.
            body: The parsed response body.

        Returns:
            A HuefyError configured based on the response.
        """
        body = body or {}
        message = body.get("message") or body.get("error") or f"API error (HTTP {status_code})"
        request_id = body.get("request_id") or body.get("requestId")

        code = _status_code_to_error_code(status_code)
        recoverable = is_recoverable_code(code)

        retry_after: float | None = None
        if "retry_after" in body:
            try:
                retry_after = float(body["retry_after"])
            except (ValueError, TypeError):
                pass

        return cls(
            message=message,
            code=code,
            status_code=status_code,
            recoverable=recoverable,
            retry_after=retry_after,
            request_id=request_id,
            details=body,
        )

    def __repr__(self) -> str:
        return (
            f"HuefyError("
            f"message={str(self)!r}, "
            f"code={self.code.value}, "
            f"status_code={self.status_code}, "
            f"recoverable={self.recoverable}"
            f")"
        )


def _status_code_to_error_code(status_code: int) -> ErrorCode:
    """Map an HTTP status code to an ErrorCode."""
    status_map: dict[int, ErrorCode] = {
        400: ErrorCode.API_BAD_REQUEST,
        401: ErrorCode.AUTH_INVALID_KEY,
        403: ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.API_NOT_FOUND,
        429: ErrorCode.API_RATE_LIMITED,
        500: ErrorCode.API_SERVER_ERROR,
        502: ErrorCode.API_SERVER_ERROR,
        503: ErrorCode.API_UNAVAILABLE,
        504: ErrorCode.API_SERVER_ERROR,
    }
    return status_map.get(status_code, ErrorCode.API_ERROR)
