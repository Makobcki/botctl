"""Integration tests for Telegram callback gateway."""

import asyncio
from pathlib import Path

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.bootstrap import CommandCatalogBootstrap
from serverbot.application.commanding.callback_factory import CallbackRequestFactory
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.infrastructure.db.sqlite_repositories import (
    SqliteAuditRepository,
    SqliteBootstrap,
    SqliteConnectionFactory,
    SqlitePrincipalTagRepository,
)
from serverbot.infrastructure.telegram_callback_gateway import TelegramCallbackGateway


def test_callback_gateway_dispatches_parsed_callback(tmp_path: Path) -> None:
    """Gateway should parse callback payload and dispatch command pipeline.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "callback-gateway.db"))
    SqliteBootstrap(connection_factory).apply()
    acl_service = AclService(SqlitePrincipalTagRepository(connection_factory))
    acl_service.grant_tag(300, "view.status")
    pipeline = CommandCatalogBootstrap(
        descriptors=(
            CommandDescriptor(
                name="status",
                required_tag="view.status",
                description="Show status",
            ),
        )
    ).build_pipeline(
        acl_service=acl_service,
        audit_service=PersistentAuditService(SqliteAuditRepository(connection_factory)),
    )
    gateway = TelegramCallbackGateway(
        request_factory=CallbackRequestFactory(
            command_registry=pipeline.command_registry,
            token_parser=CommandTokenParser(),
        ),
        command_pipeline=pipeline,
    )

    response = asyncio.run(gateway.handle_callback(principal_id=300, data="cmd:status"))

    assert response.success is True
