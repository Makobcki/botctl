"""Domain-level exceptions and error codes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainError(Exception):
    """Base domain error with machine-readable error code.

    Args:
        message: Human-readable error text.
        error_code: Stable machine-readable code.

    Returns:
        None
    """

    message: str
    error_code: str

    def __str__(self) -> str:
        """Return formatted error string.

        Args:
            None.

        Returns:
            String representation with error code.

        Raises:
            None.
        """

        return f"{self.error_code}: {self.message}"


@dataclass(frozen=True)
class AuthorizationError(DomainError):
    """Error raised when command execution is not authorized.

    Args:
        message: Human-readable error text.
        error_code: Stable machine-readable code.

    Returns:
        None
    """


@dataclass(frozen=True)
class CommandExecutionError(DomainError):
    """Error raised when external command execution fails.

    Args:
        message: Human-readable error text.
        error_code: Stable machine-readable code.

    Returns:
        None
    """
