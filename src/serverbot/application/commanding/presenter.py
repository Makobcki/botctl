"""Presentation helpers for command responses and domain errors."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.domain.commanding.models import CommandResponse
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CommandPresenter:
    """Map pipeline results and errors to user-facing text messages.

    Args:
        None.
    """

    def present_success(self, response: CommandResponse) -> str:
        """Render successful command response.

        Args:
            response: Command response payload.

        Returns:
            User-facing response text.

        Raises:
            None.
        """

        return response.message

    def present_domain_error(self, error: DomainError) -> str:
        """Render domain-level errors to user-friendly text.

        Args:
            error: Domain exception payload.

        Returns:
            User-facing error text.

        Raises:
            None.
        """

        return f"{error.error_code}: {error.message}"

    def present_internal_error(self) -> str:
        """Render fallback message for unexpected failures.

        Args:
            None.

        Returns:
            Generic user-facing failure text.

        Raises:
            None.
        """

        return "Internal error occurred. Please try again later."
