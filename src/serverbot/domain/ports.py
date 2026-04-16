"""Domain ports for adapter-driven architecture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    """Result of external command execution.

    Args:
        return_code: Process return code.
        stdout: Standard output value.
        stderr: Standard error value.

    Returns:
        None
    """

    return_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    """Abstraction for subprocess command execution."""

    async def run(self, command: list[str]) -> CommandResult:
        """Execute command asynchronously.

        Args:
            command: Validated command vector.

        Returns:
            Structured command result.

        Raises:
            Exception: Adapter-specific execution errors.
        """


@dataclass(frozen=True)
class AppConfig:
    """Core application configuration loaded from KDL.

    Args:
        telegram_token: Telegram bot token.
        alert_chat_id: Alert destination chat.
        verbose: Verbose logging flag.
        worker_interval_seconds: Worker interval timeout.
        allowed_units: Allowed systemd units.
        allowed_zones: Allowed DNS zones.
    """

    telegram_token: str
    alert_chat_id: int
    verbose: bool
    worker_interval_seconds: int
    allowed_units: tuple[str, ...]
    allowed_zones: tuple[str, ...]


class ConfigLoader(Protocol):
    """Abstraction for configuration loading adapters."""

    def load(self, path: str) -> AppConfig:
        """Load application configuration.

        Args:
            path: Configuration file path.

        Returns:
            Immutable application configuration.

        Raises:
            Exception: Loader-specific parse errors.
        """
