"""Shared token parsing helpers for command request factories."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.domain.commanding.models import CommandArgumentDescriptor
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class CommandTokenParser:
    """Parse command tokens into structured argument dictionary.

    Args:
        None.
    """

    def parse_arguments(
        self,
        tokens: list[str],
        argument_descriptors: tuple[CommandArgumentDescriptor, ...],
    ) -> dict[str, str]:
        """Parse named and positional tokens into argument mapping.

        Args:
            tokens: Raw argument tokens.
            argument_descriptors: Ordered descriptor list.

        Returns:
            Parsed argument mapping.

        Raises:
            DomainError: If token syntax is invalid.
        """

        if not argument_descriptors:
            return {}
        result: dict[str, str] = {}
        positional_index = 0
        descriptor_names = [descriptor.name for descriptor in argument_descriptors]
        for token in tokens:
            if "=" in token:
                name, value = token.split("=", maxsplit=1)
                if name not in descriptor_names:
                    raise DomainError(
                        f"Unknown argument '{name}'.",
                        "COMMAND_TEXT_UNKNOWN_ARGUMENT",
                    )
                result[name] = value
                continue
            if positional_index >= len(argument_descriptors):
                raise DomainError(
                    "Too many positional arguments.",
                    "COMMAND_TEXT_TOO_MANY_POSITIONALS",
                )
            target_name = argument_descriptors[positional_index].name
            result[target_name] = token
            positional_index += 1
        return result
