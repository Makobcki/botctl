"""Unit tests for RPZ application service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from serverbot.application.rpz_service import RpzService
from serverbot.domain.ports import CommandResult
from serverbot.domain.repositories import RpzRuleRecord
from serverbot.infrastructure.command_catalog import CommandCatalog


@dataclass
class InMemoryRpzRepository:
    """In-memory RPZ repository for service tests.

    Args:
        values: Stored RPZ records by (zone, qname).
    """

    values: dict[tuple[str, str], RpzRuleRecord] = field(default_factory=dict)

    def upsert(self, record: RpzRuleRecord) -> None:
        """Insert or replace record.

        Args:
            record: RPZ record payload.

        Returns:
            None.
        """

        self.values[(record.zone, record.qname)] = record

    def delete(self, zone: str, qname: str) -> bool:
        """Delete record by key.

        Args:
            zone: Zone name.
            qname: Rule qname.

        Returns:
            True if deleted.
        """

        return self.values.pop((zone, qname), None) is not None

    def list_rules(self, zone: str | None = None) -> list[RpzRuleRecord]:
        """List records by optional zone.

        Args:
            zone: Optional zone filter.

        Returns:
            Sorted list of records.
        """

        rows = list(self.values.values())
        if zone is not None:
            rows = [row for row in rows if row.zone == zone]
        return sorted(rows, key=lambda item: item.qname)

    def find_rules(self, query: str, zone: str | None = None) -> list[RpzRuleRecord]:
        """Find records by qname query.

        Args:
            query: Query substring.
            zone: Optional zone filter.

        Returns:
            Matching records.
        """

        rows = self.list_rules(zone)
        return [row for row in rows if query in row.qname]


@dataclass
class SpyRunner:
    """Runner spy for service tests.

    Args:
        commands: Executed commands.
    """

    commands: list[list[str]] = field(default_factory=list)

    async def run(self, command: list[str]) -> CommandResult:
        """Capture command and return success.

        Args:
            command: Command vector.

        Returns:
            Success command result.
        """

        self.commands.append(command)
        return CommandResult(return_code=0, stdout="ok", stderr="")


def test_rpz_service_add_and_delete_trigger_reload() -> None:
    """Service should mutate repository and reload zone.

    Args:
        None.

    Returns:
        None.
    """

    repository = InMemoryRpzRepository()
    runner = SpyRunner()
    service = RpzService(
        repository=repository,
        command_catalog=CommandCatalog(
            allowed_units=frozenset({"bind9.service"}),
            allowed_zones=frozenset({"rpz.local"}),
        ),
        command_runner=runner,
        default_zone="rpz.local",
    )

    saved = asyncio.run(service.add_rule("example.com", "nxdomain"))
    deleted = asyncio.run(service.delete_rule("example.com"))

    assert saved.qname == "example.com"
    assert deleted is True
    assert runner.commands == [["rndc", "reload", "rpz.local"], ["rndc", "reload", "rpz.local"]]
