"""Domain models for ACL and command authorization."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    """Known actor in ACL table.

    Args:
        telegram_id: Telegram user or chat identifier.
        tags: Permission tags assigned to actor.
    """

    telegram_id: int
    tags: frozenset[str]


@dataclass(frozen=True)
class CommandPolicy:
    """Required tag for command execution.

    Args:
        command_name: Telegram command name.
        required_tag: ACL tag required for command.
    """

    command_name: str
    required_tag: str
