"""Registry of available command descriptors and handlers."""

from __future__ import annotations

from dataclasses import dataclass, field

from serverbot.application.commanding.contracts import CommandHandler
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class RegisteredCommand:
    """Bound pair of descriptor and executable handler.

    Args:
        descriptor: Static command metadata.
        handler: Runtime command handler.
    """

    descriptor: CommandDescriptor
    handler: CommandHandler


@dataclass
class CommandRegistry:
    """Mutable registry for command wiring during bootstrap.

    Args:
        _entries: Internal command map.
    """

    _entries: dict[str, RegisteredCommand] = field(default_factory=dict)

    def register(self, descriptor: CommandDescriptor, handler: CommandHandler) -> None:
        """Register one command descriptor and handler.

        Args:
            descriptor: Static metadata for command.
            handler: Runtime handler implementation.

        Returns:
            None.

        Raises:
            DomainError: If command already exists in registry.
        """

        if descriptor.name in self._entries:
            raise DomainError(
                f"Command already registered: {descriptor.name}",
                "COMMAND_ALREADY_REGISTERED",
            )
        self._entries[descriptor.name] = RegisteredCommand(descriptor=descriptor, handler=handler)

    def get(self, command_name: str) -> RegisteredCommand:
        """Fetch registered command by name.

        Args:
            command_name: Internal command name.

        Returns:
            Registered command metadata and handler.

        Raises:
            DomainError: If command is missing.
        """

        command = self._entries.get(command_name)
        if command is None:
            raise DomainError(f"Unknown command: {command_name}", "COMMAND_NOT_FOUND")
        return command

    def list_descriptors(self) -> tuple[CommandDescriptor, ...]:
        """Return immutable command metadata collection.

        Args:
            None.

        Returns:
            Tuple of registered command descriptors.

        Raises:
            None.
        """

        return tuple(item.descriptor for item in self._entries.values())
