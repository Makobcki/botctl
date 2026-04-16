"""Async subprocess command runner adapter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from serverbot.domain.errors import CommandExecutionError
from serverbot.domain.ports import CommandResult, CommandRunner


@dataclass(frozen=True)
class AsyncSubprocessRunner(CommandRunner):
    """Execute external commands without blocking event loop.

    Args:
        None.

    Returns:
        None.
    """

    async def run(self, command: list[str]) -> CommandResult:
        """Run subprocess command and collect output.

        Args:
            command: Validated command vector.

        Returns:
            Captured process result.

        Raises:
            CommandExecutionError: If command cannot be executed.
        """

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise CommandExecutionError(str(exc), "COMMAND_START_FAILED") from exc

        stdout, stderr = await process.communicate()
        return CommandResult(
            return_code=process.returncode,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
        )
