"""System-facing application services."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.domain.errors import CommandExecutionError
from serverbot.domain.ports import CommandRunner
from serverbot.infrastructure.command_catalog import CommandCatalog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemdService:
    """Service for safe `journalctl` command execution.

    Args:
        command_catalog: Whitelisted command catalog.
        command_runner: Async command runner adapter.
    """

    command_catalog: CommandCatalog
    command_runner: CommandRunner

    async def tail_journal(self, unit: str, lines: int) -> str:
        """Read latest journal lines for allowed unit.

        Args:
            unit: Allowed systemd unit.
            lines: Line limit.

        Returns:
            Journal output text.

        Raises:
            CommandExecutionError: If journalctl returns non-zero code.
        """

        command = self.command_catalog.journal_unit(unit, lines)
        logger.debug("Executing command: %s", " ".join(command))
        result = await self.command_runner.run(command)
        if result.return_code != 0:
            raise CommandExecutionError(result.stderr.strip(), "JOURNAL_COMMAND_FAILED")
        return result.stdout
