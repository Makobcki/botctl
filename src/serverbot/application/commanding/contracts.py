"""Contracts for command handlers and registries."""

from __future__ import annotations

from typing import Protocol

from serverbot.domain.commanding.models import CommandRequest, CommandResponse


class CommandHandler(Protocol):
    """Asynchronous handler contract for command execution."""

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Handle command request.

        Args:
            request: Command request data.

        Returns:
            Structured command response.

        Raises:
            Exception: Domain-specific execution failures.
        """
