"""Integration test for async subprocess runner."""

import asyncio

from serverbot.infrastructure.system.subprocess_runner import AsyncSubprocessRunner


def test_subprocess_runner_executes_command() -> None:
    """Runner should execute command and return output.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    runner = AsyncSubprocessRunner()

    result = asyncio.run(runner.run(["python3", "-c", "print('runner-ok')"]))

    assert result.return_code == 0
    assert "runner-ok" in result.stdout
