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
