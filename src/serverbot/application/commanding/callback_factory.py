"""Factory converting callback payloads into command requests."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandRequest
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CallbackRequestFactory:
    """Create command requests from callback data payload.

    Args:
        command_registry: Registered command metadata source.
        token_parser: Shared token parser dependency.
    """

    command_registry: CommandRegistry
    token_parser: CommandTokenParser

    def from_callback_data(self, principal_id: int, data: str) -> CommandRequest:
        """Parse callback payload into command request.

        Args:
            principal_id: Telegram principal identifier.
            data: Callback data payload.

        Returns:
            Structured command request.

        Raises:
            DomainError: If payload format is invalid.
        """

        tokens = [token for token in data.strip().split(" ") if token]
        if not tokens:
            raise DomainError("Callback payload is empty.", "CALLBACK_EMPTY")
        if not tokens[0].startswith("cmd:"):
            raise DomainError("Callback must start with 'cmd:'.", "CALLBACK_INVALID_PREFIX")
        command_name = tokens[0][4:]
        if not command_name:
            raise DomainError("Callback command name is empty.", "CALLBACK_MISSING_COMMAND")
        descriptor = self.command_registry.get(command_name).descriptor
        arguments = self.token_parser.parse_arguments(tokens[1:], descriptor.arguments)
        return CommandRequest(
            principal_id=principal_id,
            command_name=command_name,
            arguments=arguments,
        )
