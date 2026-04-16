"""Integration tests for command pipeline foundation."""

import asyncio
from pathlib import Path

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.bootstrap import CommandCatalogBootstrap
from serverbot.domain.commanding.models import CommandDescriptor, CommandRequest
from serverbot.infrastructure.db.sqlite_repositories import (
    SqliteAuditRepository,
    SqliteBootstrap,
    SqliteConnectionFactory,
    SqlitePrincipalTagRepository,
)


def test_pipeline_dispatches_adapter_backed_status(tmp_path: Path) -> None:
    """Pipeline should execute adapter-backed status for allowed principal.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "pipeline.db"))
    SqliteBootstrap(connection_factory).apply()
    acl_service = AclService(SqlitePrincipalTagRepository(connection_factory))
    acl_service.grant_tag(100, "view.status")
    audit_service = PersistentAuditService(SqliteAuditRepository(connection_factory))

    bootstrap = CommandCatalogBootstrap(
        descriptors=(
            CommandDescriptor(
                name="status",
                required_tag="view.status",
                description="Show server status",
            ),
        )
    )
    pipeline = bootstrap.build_pipeline(acl_service=acl_service, audit_service=audit_service)

    response = asyncio.run(
        pipeline.dispatch(
            CommandRequest(principal_id=100, command_name="status", arguments={})
        )
    )

    assert response.success is True
    assert response.message


def test_pipeline_denies_without_tag_and_audits(tmp_path: Path) -> None:
    """Pipeline should deny command when principal misses required tag.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "pipeline.db"))
    SqliteBootstrap(connection_factory).apply()
    acl_service = AclService(SqlitePrincipalTagRepository(connection_factory))
    audit_repository = SqliteAuditRepository(connection_factory)
    audit_service = PersistentAuditService(audit_repository)

    bootstrap = CommandCatalogBootstrap(
        descriptors=(
            CommandDescriptor(
                name="status",
                required_tag="view.status",
                description="Show server status",
            ),
        )
    )
    pipeline = bootstrap.build_pipeline(acl_service=acl_service, audit_service=audit_service)

    response = asyncio.run(
        pipeline.dispatch(
            CommandRequest(principal_id=200, command_name="status", arguments={})
        )
    )

    assert response.success is False
    records = audit_repository.list_recent(1)
    assert records[0].success is False
