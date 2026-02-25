"""Logging abstractions for the Huefy SDK."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


class Logger(ABC):
    """Abstract logger interface for the SDK.

    Implement this protocol to integrate with your application's logging framework.
    """

    @abstractmethod
    def debug(self, message: str, *args: Any) -> None:
        """Log a debug message."""
        ...

    @abstractmethod
    def info(self, message: str, *args: Any) -> None:
        """Log an informational message."""
        ...

    @abstractmethod
    def warn(self, message: str, *args: Any) -> None:
        """Log a warning message."""
        ...

    @abstractmethod
    def error(self, message: str, *args: Any) -> None:
        """Log an error message."""
        ...


class ConsoleLogger(Logger):
    """Logger implementation that writes to the Python standard logging module."""

    def __init__(self, name: str = "huefy", level: int = logging.DEBUG) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
            )
            self._logger.addHandler(handler)
        self._logger.setLevel(level)

    def debug(self, message: str, *args: Any) -> None:
        self._logger.debug(message, *args)

    def info(self, message: str, *args: Any) -> None:
        self._logger.info(message, *args)

    def warn(self, message: str, *args: Any) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args: Any) -> None:
        self._logger.error(message, *args)


class NoopLogger(Logger):
    """Logger implementation that silently discards all messages."""

    def debug(self, message: str, *args: Any) -> None:
        pass

    def info(self, message: str, *args: Any) -> None:
        pass

    def warn(self, message: str, *args: Any) -> None:
        pass

    def error(self, message: str, *args: Any) -> None:
        pass


def create_logger(debug: bool = False) -> Logger:
    """Create a logger instance.

    Args:
        debug: If True, return a ConsoleLogger at DEBUG level.
               If False, return a NoopLogger that discards all output.

    Returns:
        A Logger instance.
    """
    if debug:
        return ConsoleLogger(level=logging.DEBUG)
    return NoopLogger()
