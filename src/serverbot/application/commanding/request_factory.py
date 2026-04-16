"""Factory converting Telegram command text into command requests."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandRequest
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CommandRequestFactory:
    """Build validated `CommandRequest` instances from raw text input.

    Args:
        command_registry: Registered command metadata source.
        token_parser: Shared token parsing utility.
    """

    command_registry: CommandRegistry
    token_parser: CommandTokenParser

    def from_telegram_text(self, principal_id: int, text: str) -> CommandRequest:
        """Parse Telegram text into structured command request.

        Args:
            principal_id: Telegram principal identifier.
            text: Raw message text.

        Returns:
            Structured command request with parsed arguments.

        Raises:
            DomainError: If text format or command name is invalid.
        """

        stripped = text.strip()
        if not stripped.startswith("/"):
            raise DomainError("Command must start with '/'.", "COMMAND_TEXT_INVALID_PREFIX")
        tokens = [token for token in stripped[1:].split(" ") if token]
        if not tokens:
            raise DomainError("Command name is required.", "COMMAND_TEXT_MISSING_NAME")
        command_name = tokens[0]
        descriptor = self.command_registry.get(command_name).descriptor
        arguments = self.token_parser.parse_arguments(tokens[1:], descriptor.arguments)
        return CommandRequest(
            principal_id=principal_id,
            command_name=command_name,
            arguments=arguments,
            raw_tokens=tuple(tokens[1:]),
        )
