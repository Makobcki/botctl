"""Unit tests for operational adapter-backed handlers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import pytest

from serverbot.application.commanding.ops_adapter_handlers import OpsAdapterCommandHandler
from serverbot.domain.commanding.models import CommandRequest
from serverbot.domain.errors import DomainError
from serverbot.domain.ports import CommandResult
from serverbot.domain.repositories import RpzRuleRecord
from serverbot.infrastructure.command_catalog import CommandCatalog


@dataclass
class SpyRunner:
    """Simple command-runner spy for handler tests.

    Args:
        calls: Collected command invocations.
        return_code: Return code to return.
        stdout: Standard output value.
        stderr: Standard error value.
    """

    calls: list[list[str]] = field(default_factory=list)
    return_code: int = 0
    stdout: str = "ok"
    stderr: str = ""

    async def run(self, command: list[str]) -> CommandResult:
        """Capture command and return deterministic result.

        Args:
            command: Executed command vector.

        Returns:
            Fake command result.
        """

        self.calls.append(command)
        return CommandResult(return_code=self.return_code, stdout=self.stdout, stderr=self.stderr)


@dataclass
class FakeRpzService:
    """RPZ service fake for ops handler tests.

    Args:
        data: Stored RPZ rows.
    """

    data: list[RpzRuleRecord] = field(default_factory=list)

    async def add_rule(self, qname: str, policy: str, value: str = "") -> RpzRuleRecord:
        """Persist fake rule.

        Args:
            qname: RPZ qname.
            policy: RPZ policy.
            value: Optional value.

        Returns:
            Persisted record.
        """

        record = RpzRuleRecord(zone="rpz.local", qname=qname, policy=policy, value=value)
        self.data.append(record)
        return record

    async def delete_rule(self, qname: str) -> bool:
        """Delete fake rule by qname.

        Args:
            qname: RPZ qname.

        Returns:
            True when deleted.
        """

        before = len(self.data)
        self.data = [item for item in self.data if item.qname != qname]
        return len(self.data) != before

    def list_rules(self) -> list[RpzRuleRecord]:
        """Return all fake rules.

        Args:
            None.

        Returns:
            List of records.
        """

        return list(self.data)

    def find_rules(self, query: str) -> list[RpzRuleRecord]:
        """Find fake rules by query.

        Args:
            query: Query substring.

        Returns:
            Matching records.
        """

        return [item for item in self.data if query in item.qname]


def _build_handler(command_name: str, runner: SpyRunner) -> OpsAdapterCommandHandler:
    """Build operation handler with reusable command catalog.

    Args:
        command_name: Root command name.
        runner: Command runner spy.

    Returns:
        Configured operational handler.
    """

    return OpsAdapterCommandHandler(
        command_name=command_name,
        command_catalog=CommandCatalog(
            allowed_units=frozenset({"bind9.service"}),
            allowed_zones=frozenset({"rpz.local"}),
        ),
        command_runner=runner,
        rpz_service=FakeRpzService(),
    )


def test_docker_restart_uses_catalog_command() -> None:
    """Docker restart should call validated docker template.

    Args:
        None.

    Returns:
        None.
    """

    runner = SpyRunner(stdout="restarted")
    handler = _build_handler("docker", runner)
    response = asyncio.run(
        handler.handle(CommandRequest(principal_id=1, command_name="docker", raw_tokens=("restart", "api")))
    )
    assert response.success is True
    assert runner.calls[-1] == ["docker", "restart", "api"]


def test_services_reject_unknown_unit() -> None:
    """Services handler should fail fast for unknown unit.

    Args:
        None.

    Returns:
        None.
    """

    runner = SpyRunner()
    handler = _build_handler("services", runner)
    with pytest.raises(DomainError):
        asyncio.run(
            handler.handle(
                CommandRequest(
                    principal_id=1,
                    command_name="services",
                    raw_tokens=("status", "unknown.service"),
                )
            )
        )


def test_bind_reload_zone_calls_rndc_with_zone() -> None:
    """Bind reload-zone should call zone-specific reload template.

    Args:
        None.

    Returns:
        None.
    """

    runner = SpyRunner(stdout="reloaded")
    handler = _build_handler("bind", runner)
    response = asyncio.run(
        handler.handle(CommandRequest(principal_id=1, command_name="bind", raw_tokens=("reload-zone", "rpz.local")))
    )
    assert response.success is True
    assert runner.calls[-1] == ["rndc", "reload", "rpz.local"]


def test_exec_journal_unit_parses_optional_line_count() -> None:
    """Exec journal template should map args into journalctl command.

    Args:
        None.

    Returns:
        None.
    """

    runner = SpyRunner(stdout="entries")
    handler = _build_handler("exec", runner)
    response = asyncio.run(
        handler.handle(
            CommandRequest(principal_id=1, command_name="exec", raw_tokens=("journal_unit", "bind9.service", "50"))
        )
    )
    assert response.success is True
    assert runner.calls[-1] == ["journalctl", "--unit", "bind9.service", "-n", "50", "--no-pager"]


def test_rpz_add_and_del_use_repository_backed_service() -> None:
    """RPZ add/del should mutate through RPZ service dependency.

    Args:
        None.

    Returns:
        None.
    """

    runner = SpyRunner()
    service = FakeRpzService()
    handler = OpsAdapterCommandHandler(
        command_name="rpz",
        command_catalog=CommandCatalog(
            allowed_units=frozenset({"bind9.service"}),
            allowed_zones=frozenset({"rpz.local"}),
        ),
        command_runner=runner,
        rpz_service=service,
    )

    add_response = asyncio.run(
        handler.handle(CommandRequest(principal_id=1, command_name="rpz", raw_tokens=("add", "bad.site", "nxdomain")))
    )
    del_response = asyncio.run(
        handler.handle(CommandRequest(principal_id=1, command_name="rpz", raw_tokens=("del", "bad.site")))
    )

    assert add_response.success is True
    assert del_response.success is True
