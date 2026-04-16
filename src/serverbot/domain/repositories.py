"""Repository contracts for persistence adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AuditRecord:
    """Audit row content.

    Args:
        principal_id: Telegram principal identifier.
        command_name: Executed command name.
        success: Whether the command completed successfully.
    """

    principal_id: int
    command_name: str
    success: bool


class PrincipalTagRepository(Protocol):
    """Repository abstraction for principal-tag relationships."""

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Read principal tags.

        Args:
            principal_id: Telegram principal identifier.

        Returns:
            Immutable set of tag names.

        Raises:
            Exception: Storage-level read errors.
        """

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Replace principal tag assignments.

        Args:
            principal_id: Telegram principal identifier.
            tags: Desired immutable tag set.

        Returns:
            None.

        Raises:
            Exception: Storage-level write errors.
        """


class AuditRepository(Protocol):
    """Repository abstraction for command audit records."""

    def append(self, record: AuditRecord) -> None:
        """Persist an audit record.

        Args:
            record: Structured audit payload.

        Returns:
            None.

        Raises:
            Exception: Storage-level write errors.
        """

    def list_recent(self, limit: int) -> list[AuditRecord]:
        """Fetch recent audit records ordered by insertion.

        Args:
            limit: Maximum number of rows.

        Returns:
            Ordered list of records.

        Raises:
            Exception: Storage-level read errors.
        """


@dataclass(frozen=True)
class RpzRuleRecord:
    """RPZ rule row content.

    Args:
        zone: RPZ zone name.
        qname: Trigger DNS name.
        policy: RPZ policy kind (`nxdomain`, `nodata`, `cname`).
        value: Optional policy value.
    """

    zone: str
    qname: str
    policy: str
    value: str = ""


class RpzRuleRepository(Protocol):
    """Repository abstraction for RPZ rules."""

    def upsert(self, record: RpzRuleRecord) -> None:
        """Create or update RPZ rule.

        Args:
            record: RPZ record payload.

        Returns:
            None.

        Raises:
            Exception: Storage-level write errors.
        """

    def delete(self, zone: str, qname: str) -> bool:
        """Delete RPZ rule by zone and qname.

        Args:
            zone: Zone name.
            qname: Rule qname.

        Returns:
            True when a record was deleted.

        Raises:
            Exception: Storage-level write errors.
        """

    def list_rules(self, zone: str | None = None) -> list[RpzRuleRecord]:
        """List RPZ rules.

        Args:
            zone: Optional zone filter.

        Returns:
            Sorted list of RPZ records.

        Raises:
            Exception: Storage-level read errors.
        """

    def find_rules(self, query: str, zone: str | None = None) -> list[RpzRuleRecord]:
        """Find RPZ rules by qname substring.

        Args:
            query: Search query string.
            zone: Optional zone filter.

        Returns:
            Matching RPZ records.

        Raises:
            Exception: Storage-level read errors.
        """
