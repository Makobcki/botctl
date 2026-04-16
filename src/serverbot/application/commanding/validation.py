"""Argument validation for configured command descriptors."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CommandArgumentValidator:
    """Validate runtime command arguments against descriptor schema.

    Args:
        None.
    """

    def validate(self, descriptor: CommandDescriptor, arguments: dict[str, str]) -> None:
        """Validate request arguments against command schema.

        Args:
            descriptor: Command descriptor with argument declarations.
            arguments: Incoming argument mapping.

        Returns:
            None.

        Raises:
            DomainError: If unknown, missing, or invalid arguments are detected.
        """

        known_names = {argument.name for argument in descriptor.arguments}
        unknown_names = sorted(set(arguments) - known_names)
        if unknown_names:
            raise DomainError(
                f"Unknown arguments for {descriptor.name}: {', '.join(unknown_names)}",
                "COMMAND_ARG_UNKNOWN",
            )

        for argument in descriptor.arguments:
            self._validate_one(descriptor.name, argument, arguments)

    def _validate_one(
        self,
        command_name: str,
        argument: CommandArgumentDescriptor,
        arguments: dict[str, str],
    ) -> None:
        """Validate one argument value by descriptor definition.

        Args:
            command_name: Internal command name.
            argument: One argument descriptor.
            arguments: Incoming argument mapping.

        Returns:
            None.

        Raises:
            DomainError: If value is missing or has invalid type.
        """

        value = arguments.get(argument.name)
        if argument.required and value is None:
            raise DomainError(
                f"Missing required argument '{argument.name}' for command '{command_name}'.",
                "COMMAND_ARG_REQUIRED",
            )
        if value is None:
            return
        if argument.value_type == "str":
            return
        if argument.value_type == "int":
            self._ensure_integer(command_name, argument.name, value)
            return
        raise DomainError(
            f"Unsupported argument type '{argument.value_type}' for '{argument.name}'.",
            "COMMAND_ARG_TYPE_UNSUPPORTED",
        )

    def _ensure_integer(self, command_name: str, argument_name: str, value: str) -> None:
        """Validate integer argument content.

        Args:
            command_name: Internal command name.
            argument_name: Argument name.
            value: Raw value.

        Returns:
            None.

        Raises:
            DomainError: If value cannot be parsed as integer.
        """

        try:
            int(value)
        except ValueError as exc:
            raise DomainError(
                f"Argument '{argument_name}' for '{command_name}' must be int.",
                "COMMAND_ARG_TYPE_INVALID",
            ) from exc
