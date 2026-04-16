"""Unit tests for adapter-backed command handlers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import pytest

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.adapter_handlers import (
    AclAdapterCommandHandler,
    AuditAdapterCommandHandler,
    WhoAmIAdapterCommandHandler,
)
from serverbot.domain.commanding.models import CommandRequest
from serverbot.domain.errors import DomainError
from serverbot.domain.repositories import AuditRecord


@dataclass
class InMemoryPrincipalTagRepository:
    """In-memory principal/tag repository for tests.

    Args:
        values: Mutable principal -> tags mapping.
    """

    values: dict[int, frozenset[str]] = field(default_factory=dict)

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Return tags for a principal.

        Args:
            principal_id: Principal identifier.

        Returns:
            Immutable set of tags.
        """

        return self.values.get(principal_id, frozenset())

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Persist tags for a principal.

        Args:
            principal_id: Principal identifier.
            tags: Immutable tag set.

        Returns:
            None.
        """

        self.values[principal_id] = tags

    def has_principals(self) -> bool:
        """Check whether any principal exists in fake repository.

        Args:
            None.

        Returns:
            True when repository contains principals.
        """

        return bool(self.values)


@dataclass
class InMemoryAuditRepository:
    """In-memory audit repository for tests.

    Args:
        rows: Stored audit rows.
    """

    rows: list[AuditRecord] = field(default_factory=list)

    def append(self, record: AuditRecord) -> None:
        """Append one audit record.

        Args:
            record: Audit payload.

        Returns:
            None.
        """

        self.rows.append(record)

    def list_recent(self, limit: int) -> list[AuditRecord]:
        """Return latest records in reverse insertion order.

        Args:
            limit: Maximum rows.

        Returns:
            Newest-first list.
        """

        return list(reversed(self.rows))[:limit]


def test_acl_adapter_grant_and_list() -> None:
    """ACL adapter should grant a tag and show it in list output.

    Args:
        None.

    Returns:
        None.
    """

    repository = InMemoryPrincipalTagRepository()
    handler = AclAdapterCommandHandler(acl_service=AclService(repository))
    asyncio.run(handler.handle(CommandRequest(principal_id=1, command_name="acl", raw_tokens=("grant", "10", "ops.bind"))))
    response = asyncio.run(handler.handle(CommandRequest(principal_id=10, command_name="acl", raw_tokens=("list",))))
    assert response.success is True
    assert "ops.bind" in response.message


def test_acl_adapter_rejects_invalid_principal() -> None:
    """ACL adapter should reject malformed principal argument.

    Args:
        None.

    Returns:
        None.
    """

    handler = AclAdapterCommandHandler(acl_service=AclService(InMemoryPrincipalTagRepository()))
    with pytest.raises(DomainError):
        asyncio.run(
            handler.handle(
                CommandRequest(principal_id=1, command_name="acl", raw_tokens=("grant", "x-user", "ops.bind"))
            )
        )


def test_audit_adapter_renders_recent_rows() -> None:
    """Audit adapter should render recent audit rows with limit.

    Args:
        None.

    Returns:
        None.
    """

    audit_repository = InMemoryAuditRepository(
        rows=[
            AuditRecord(principal_id=1, command_name="status", success=True),
            AuditRecord(principal_id=2, command_name="docker", success=False),
        ]
    )
    handler = AuditAdapterCommandHandler(audit_service=PersistentAuditService(audit_repository))
    response = asyncio.run(handler.handle(CommandRequest(principal_id=1, command_name="audit", raw_tokens=("last", "1"))))
    assert response.success is True
    assert "principal=2 command=docker success=False" in response.message


def test_whoami_adapter_renders_principal_tags() -> None:
    """WhoAmI adapter should return principal identity and tags.

    Args:
        None.

    Returns:
        None.
    """

    repository = InMemoryPrincipalTagRepository(values={42: frozenset({"view.status", "ops.bind"})})
    handler = WhoAmIAdapterCommandHandler(acl_service=AclService(repository))
    response = asyncio.run(handler.handle(CommandRequest(principal_id=42, command_name="whoami")))
    assert response.success is True
    assert "Principal: 42" in response.message
    assert "view.status" in response.message
