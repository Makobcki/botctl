"""Domain models for command orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandArgumentDescriptor:
    """Static metadata for one command argument.

    Args:
        name: Argument name.
        value_type: Supported value type (`str` or `int`).
        required: Whether argument is mandatory.
    """

    name: str
    value_type: str
    required: bool


@dataclass(frozen=True)
class CommandDescriptor:
    """Static metadata for a supported command.

    Args:
        name: Stable internal command name.
        required_tag: ACL tag required to execute command.
        description: Human-readable description of command purpose.
        arguments: Immutable argument descriptor list.
    """

    name: str
    required_tag: str
    description: str
    arguments: tuple[CommandArgumentDescriptor, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommandRequest:
    """User request to execute a command.

    Args:
        principal_id: Telegram principal identifier.
        command_name: Internal command name.
        arguments: Immutable argument dictionary.
    """

    principal_id: int
    command_name: str
    arguments: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResponse:
    """Structured response of command pipeline.

    Args:
        command_name: Executed command name.
        message: User-facing response message.
        success: Execution status.
    """

    command_name: str
    message: str
    success: bool
