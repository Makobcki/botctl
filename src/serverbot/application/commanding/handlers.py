"""Base handlers used as placeholders before command actions are implemented."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.contracts import CommandHandler
from serverbot.domain.commanding.models import CommandRequest, CommandResponse


@dataclass(frozen=True)
class PlaceholderHandler(CommandHandler):
    """Handler returning deterministic placeholder message.

    Args:
        response_message: Placeholder text for command execution.
    """

    response_message: str

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Return placeholder response without side effects.

        Args:
            request: Incoming command request.

        Returns:
            Successful command response with placeholder text.

        Raises:
            None.
        """

        return CommandResponse(
            command_name=request.command_name,
            message=self.response_message,
            success=True,
        )
