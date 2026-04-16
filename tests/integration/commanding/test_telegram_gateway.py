"""Integration tests for Telegram command gateway adapter."""

import asyncio
from pathlib import Path

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.bootstrap import CommandCatalogBootstrap
from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
from serverbot.infrastructure.db.sqlite_repositories import (
    SqliteAuditRepository,
    SqliteBootstrap,
    SqliteConnectionFactory,
    SqlitePrincipalTagRepository,
)
from serverbot.infrastructure.telegram_parser import TelegramCommandGateway


def test_telegram_gateway_dispatches_parsed_command(tmp_path: Path) -> None:
    """Gateway should parse telegram text and dispatch pipeline.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "gateway.db"))
    SqliteBootstrap(connection_factory).apply()
    acl_service = AclService(SqlitePrincipalTagRepository(connection_factory))
    acl_service.grant_tag(300, "view.logs")
    pipeline = CommandCatalogBootstrap(
        descriptors=(
            CommandDescriptor(
                name="logs",
                required_tag="view.logs",
                description="Read logs",
                arguments=(
                    CommandArgumentDescriptor(name="lines", value_type="int", required=False),
                ),
            ),
        )
    ).build_pipeline(
        acl_service=acl_service,
        audit_service=PersistentAuditService(SqliteAuditRepository(connection_factory)),
    )

    gateway = TelegramCommandGateway(
        request_factory=CommandRequestFactory(pipeline.command_registry, CommandTokenParser()),
        command_pipeline=pipeline,
    )

    response = asyncio.run(gateway.handle_text(300, "/logs lines=50"))

    assert response.success is True
