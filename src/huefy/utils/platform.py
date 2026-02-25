"""Platform detection and user-agent utilities."""

from __future__ import annotations

import sys

from huefy.utils.version import SDK_VERSION


def get_platform() -> str:
    """Detect the current operating system platform.

    Returns:
        One of 'linux', 'darwin', 'windows', or 'unknown'.
    """
    platform = sys.platform.lower()
    if platform.startswith("linux"):
        return "linux"
    if platform == "darwin":
        return "darwin"
    if platform in ("win32", "cygwin", "msys"):
        return "windows"
    return "unknown"


def get_sdk_user_agent() -> str:
    """Build the SDK User-Agent string.

    Returns:
        A user-agent string in the format ``huefy-sdk-python/{version}``.
    """
    return f"huefy-sdk-python/{SDK_VERSION}"
