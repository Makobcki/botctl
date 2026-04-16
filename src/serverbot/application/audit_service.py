"""Persistent audit application service."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.domain.repositories import AuditRecord, AuditRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PersistentAuditService:
    """Audit service that stores records in repository.

    Args:
        audit_repository: Audit repository dependency.
    """

    audit_repository: AuditRepository

    def record(self, principal_id: int, command_name: str, success: bool) -> None:
        """Write one audit entry.

        Args:
            principal_id: Telegram principal identifier.
            command_name: Executed command.
            success: Execution status.

        Returns:
            None.

        Raises:
            Exception: Propagates storage adapter errors.
        """

        self.audit_repository.append(
            AuditRecord(principal_id=principal_id, command_name=command_name, success=success)
        )
        logger.info("Audit persisted principal=%s command=%s success=%s", principal_id, command_name, success)

    def list_recent(self, limit: int) -> list[AuditRecord]:
        """Read recent audit records.

        Args:
            limit: Maximum number of rows.

        Returns:
            Newest-first list of audit records.

        Raises:
            Exception: Propagates storage adapter errors.
        """

        return self.audit_repository.list_recent(limit)
