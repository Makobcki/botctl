"""Domain models for scripted command execution loaded from KDL."""

from __future__ import annotations

from dataclasses import dataclass, field

from serverbot.domain.commanding.models import CommandDescriptor


@dataclass(frozen=True)
class CommandActionBlock:
    """Executable action block.

    Args:
        stream: Whether command output should be streamed.
        statuses: Status message mapping keyed by status id.
        prints: Messages that should be printed.
        command_template: Shell command template.
    """

    stream: bool = False
    statuses: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    prints: tuple[str, ...] = field(default_factory=tuple)
    command_template: str | None = None


@dataclass(frozen=True)
class CommandExceptRule:
    """One conditional branch for non-zero exit codes.

    Args:
        expression: Exit code expression (`127`, `>32`).
        execute: Action block for matching expression.
    """

    expression: str
    execute: CommandActionBlock


@dataclass(frozen=True)
class CommandScript:
    """Script definition for one command and optional subcommand.

    Args:
        name: Base command name.
        help_text: Human-readable help.
        categories: Categories of command.
        execute: Default execute block.
        subcommands: Subcommand script mapping.
        except_rules: Conditional execution rules on failure.
    """

    name: str
    help_text: str
    categories: tuple[str, ...]
    execute: CommandActionBlock
    subcommands: tuple[tuple[str, CommandActionBlock, tuple[CommandExceptRule, ...]], ...] = field(
        default_factory=tuple
    )
    except_rules: tuple[CommandExceptRule, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommandDefinition:
    """Complete configured command runtime definition.

    Args:
        descriptor: Public command descriptor for registry and help.
        root_execute: Execute block for base command.
        root_except_rules: Except rules for base command.
        subcommands: Subcommand mapping.
    """

    descriptor: CommandDescriptor
    root_execute: CommandActionBlock
    root_except_rules: tuple[CommandExceptRule, ...] = field(default_factory=tuple)
    subcommands: tuple[tuple[str, CommandScript], ...] = field(default_factory=tuple)
