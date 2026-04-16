"""Application service for repository-backed RPZ rule workflows."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.domain.errors import CommandExecutionError, DomainError
from serverbot.domain.ports import CommandRunner
from serverbot.domain.repositories import RpzRuleRecord, RpzRuleRepository
from serverbot.infrastructure.command_catalog import CommandCatalog


@dataclass(frozen=True)
class RpzService:
    """Service implementing RPZ mutation and query workflow.

    Args:
        repository: RPZ repository adapter.
        command_catalog: Command template catalog.
        command_runner: Async command runner adapter.
        default_zone: Zone used when command request does not specify one.
    """

    repository: RpzRuleRepository
    command_catalog: CommandCatalog
    command_runner: CommandRunner
    default_zone: str

    async def add_rule(self, qname: str, policy: str, value: str = "") -> RpzRuleRecord:
        """Persist RPZ rule and apply zone reload.

        Args:
            qname: RPZ qname.
            policy: RPZ policy key.
            value: Optional policy value.

        Returns:
            Persisted RPZ record.

        Raises:
            DomainError: If policy/qname are invalid.
            CommandExecutionError: If reload command fails.
        """

        zone = self._require_default_zone()
        normalized_policy = policy.lower().strip()
        if normalized_policy not in {"nxdomain", "nodata", "cname"}:
            raise DomainError("Unsupported RPZ policy.", "RPZ_POLICY_INVALID")
        normalized_qname = qname.strip().lower()
        if not normalized_qname:
            raise DomainError("RPZ qname must be non-empty.", "RPZ_QNAME_INVALID")
        record = RpzRuleRecord(
            zone=zone,
            qname=normalized_qname,
            policy=normalized_policy,
            value=value.strip(),
        )
        self.repository.upsert(record)
        await self._reload_zone(zone)
        return record

    async def delete_rule(self, qname: str) -> bool:
        """Delete RPZ rule and apply zone reload when deleted.

        Args:
            qname: RPZ qname to delete.

        Returns:
            True if rule existed and was deleted.

        Raises:
            DomainError: If qname is invalid.
            CommandExecutionError: If reload command fails.
        """

        normalized_qname = qname.strip().lower()
        if not normalized_qname:
            raise DomainError("RPZ qname must be non-empty.", "RPZ_QNAME_INVALID")
        zone = self._require_default_zone()
        deleted = self.repository.delete(zone, normalized_qname)
        if deleted:
            await self._reload_zone(zone)
        return deleted

    def list_rules(self) -> list[RpzRuleRecord]:
        """List RPZ rules from repository.

        Args:
            None.

        Returns:
            Sorted RPZ records.
        """

        zone = self._require_default_zone()
        return self.repository.list_rules(zone)

    def find_rules(self, query: str) -> list[RpzRuleRecord]:
        """Find RPZ rules by qname query.

        Args:
            query: Query substring.

        Returns:
            Matching RPZ records.

        Raises:
            DomainError: If query is empty.
        """

        normalized_query = query.strip().lower()
        if not normalized_query:
            raise DomainError("RPZ query must be non-empty.", "RPZ_QUERY_INVALID")
        zone = self._require_default_zone()
        return self.repository.find_rules(normalized_query, zone)

    def _require_default_zone(self) -> str:
        """Resolve configured default RPZ zone.

        Args:
            None.

        Returns:
            Non-empty zone name.

        Raises:
            DomainError: If default zone is not configured.
        """

        zone = self.default_zone.strip()
        if not zone:
            raise DomainError("RPZ default zone is not configured.", "RPZ_ZONE_NOT_CONFIGURED")
        return zone

    async def _reload_zone(self, zone: str) -> None:
        """Run `rndc reload <zone>` after repository mutation.

        Args:
            zone: Zone name.

        Returns:
            None.

        Raises:
            CommandExecutionError: If command execution fails.
        """

        command = self.command_catalog.bind_reload(zone)
        result = await self.command_runner.run(command)
        if result.return_code != 0:
            message = result.stderr.strip() or result.stdout.strip() or "Failed to reload RPZ zone."
            raise CommandExecutionError(message, "RPZ_RELOAD_FAILED")
