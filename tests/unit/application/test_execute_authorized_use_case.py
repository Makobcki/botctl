"""Unit tests for persistent authorized execute use-case."""

import asyncio
from dataclasses import dataclass

import pytest

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.services import PolicyService
from serverbot.application.use_cases import ExecuteAuthorizedCommandUseCase
from serverbot.domain.errors import AuthorizationError
from serverbot.domain.models import CommandPolicy
from serverbot.domain.repositories import AuditRecord


@dataclass
class InMemoryPrincipalTagRepository:
    """In-memory principal-tag repository.

    Args:
        state: Mapping of principal ids to tag sets.
    """

    state: dict[int, frozenset[str]]

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Get principal tags.

        Args:
            principal_id: Telegram principal identifier.

        Returns:
            Immutable tags.

        Raises:
            None.
        """

        return self.state.get(principal_id, frozenset())

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Set principal tags.

        Args:
            principal_id: Telegram principal identifier.
            tags: New tag set.

        Returns:
            None.

        Raises:
            None.
        """

        self.state[principal_id] = tags

    def has_principals(self) -> bool:
        """Check whether any principal exists in in-memory ACL.

        Args:
            None.

        Returns:
            True when repository contains principals.
        """

        return bool(self.state)


@dataclass
class InMemoryAuditRepository:
    """In-memory audit repository.

    Args:
        records: Stored records list.
    """

    records: list[AuditRecord]

    def append(self, record: AuditRecord) -> None:
        """Append audit record.

        Args:
            record: Audit payload.

        Returns:
            None.

        Raises:
            None.
        """

        self.records.append(record)

    def list_recent(self, limit: int) -> list[AuditRecord]:
        """Return newest records first.

        Args:
            limit: Maximum number of rows.

        Returns:
            Sliced audit records.

        Raises:
            None.
        """

        return list(reversed(self.records))[:limit]


def test_execute_authorized_use_case_raises_for_denied_command() -> None:
    """Denied command should raise authorization error and persist audit.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    principal_repo = InMemoryPrincipalTagRepository({1: frozenset({"view.status"})})
    audit_repo = InMemoryAuditRepository([])
    use_case = ExecuteAuthorizedCommandUseCase(
        acl_service=AclService(principal_repo),
        policy_service=PolicyService(
            {"bind.reload": CommandPolicy(command_name="bind.reload", required_tag="ops.bind")}
        ),
        audit_service=PersistentAuditService(audit_repo),
    )

    with pytest.raises(AuthorizationError):
        asyncio.run(use_case.execute(1, "bind.reload"))

    assert audit_repo.records[0].success is False
