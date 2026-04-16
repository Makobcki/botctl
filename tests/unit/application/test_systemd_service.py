"""Unit tests for systemd application service."""

import asyncio
import pytest

from serverbot.application.system_services import SystemdService
from serverbot.domain.errors import CommandExecutionError
from serverbot.domain.ports import CommandResult
from serverbot.infrastructure.command_catalog import CommandCatalog


class FakeCommandRunner:
    """Simple fake command runner for unit testing.

    Args:
        result: Predefined command result.
    """

    def __init__(self, result: CommandResult) -> None:
        """Initialize fake runner.

        Args:
            result: Command result to return from `run`.

        Returns:
            None.

        Raises:
            None.
        """

        self._result = result

    async def run(self, command: list[str]) -> CommandResult:
        """Return predefined result regardless of command.

        Args:
            command: Command vector.

        Returns:
            Predefined command result.

        Raises:
            None.
        """

        _ = command
        return self._result


def test_tail_journal_returns_stdout() -> None:
    """System service should return stdout on successful command.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    service = SystemdService(
        command_catalog=CommandCatalog(
            allowed_units=frozenset({"bind9.service"}),
            allowed_zones=frozenset({"rpz.local"}),
        ),
        command_runner=FakeCommandRunner(
            CommandResult(return_code=0, stdout="ok", stderr="")
        ),
    )

    result = asyncio.run(service.tail_journal("bind9.service", 50))

    assert result == "ok"


def test_tail_journal_raises_on_non_zero_exit() -> None:
    """System service should raise domain error when command fails.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    service = SystemdService(
        command_catalog=CommandCatalog(
            allowed_units=frozenset({"bind9.service"}),
            allowed_zones=frozenset({"rpz.local"}),
        ),
        command_runner=FakeCommandRunner(
            CommandResult(return_code=1, stdout="", stderr="failed")
        ),
    )

    with pytest.raises(CommandExecutionError):
        asyncio.run(service.tail_journal("bind9.service", 50))
