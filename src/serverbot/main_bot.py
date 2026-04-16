"""Telegram bot process entrypoint."""

from __future__ import annotations

import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from serverbot.application.config_service import ConfigService
from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.bootstrap_acl import AclBootstrapService
from serverbot.application.commanding.bootstrap import CommandCatalogBootstrap
from serverbot.application.commanding.callback_factory import CallbackRequestFactory
from serverbot.application.commanding.presenter import CommandPresenter
from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.application.rpz_service import RpzService
from serverbot.config.logging import configure_logging
from serverbot.config.settings import RuntimeOptions
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.infrastructure.config.command_kdl_loader import CommandKdlLoader
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader
from serverbot.infrastructure.db.sqlite_repositories import (
    SqliteAuditRepository,
    SqliteBootstrap,
    SqliteConnectionFactory,
    SqlitePrincipalTagRepository,
    SqliteRpzRuleRepository,
)
from serverbot.infrastructure.command_catalog import CommandCatalog
from serverbot.infrastructure.system.subprocess_runner import AsyncSubprocessRunner
from serverbot.infrastructure.telegram_parser import TelegramCommandGateway
from serverbot.infrastructure.telegram_callback_gateway import TelegramCallbackGateway
from serverbot.infrastructure.telegram_controller import TelegramCommandController
from serverbot.infrastructure.telegram_middlewares import (
    AccessLogMiddleware,
    CommandRequestBuildMiddleware,
    PrincipalResolverMiddleware,
)
from serverbot.infrastructure.telegram_updates import TelegramUpdateHandler, build_command_router

logger = logging.getLogger(__name__)


def _build_start_handler(
    acl_service: AclService,
    command_descriptors: tuple[CommandDescriptor, ...],
):
    """Create /start handler that bootstraps first admin on empty ACL.

    Args:
        acl_service: ACL service dependency.
        command_descriptors: Registered command descriptors.

    Returns:
        Async message handler.
    """

    full_access_tags = frozenset(descriptor.required_tag for descriptor in command_descriptors)

    async def _on_start(message: Message) -> None:
        """Handle /start command.

        Args:
            message: Incoming Telegram message.

        Returns:
            None.
        """

        if message.from_user is None:
            await message.answer("serverbot is running")
            return
        bootstrap_applied = acl_service.bootstrap_first_admin(
            principal_id=message.from_user.id,
            tags=full_access_tags,
        )
        if bootstrap_applied:
            await message.answer(
                "serverbot is running\n"
                "Вы стали первым администратором (ACL была пуста)."
            )
            return
        await message.answer("serverbot is running")

    return _on_start


async def run_bot() -> None:
    """Run telegram polling and graceful shutdown.

    Returns:
        None
    """

    runtime_options = RuntimeOptions()
    app_config = ConfigService(KdlConfigLoader()).load(runtime_options.config_path)
    command_definitions = CommandKdlLoader().load_definitions(runtime_options.command_config_path)
    command_descriptors = tuple(definition.descriptor for definition in command_definitions)
    configure_logging(app_config.verbose)
    connection_factory = SqliteConnectionFactory(app_config.db_path)
    SqliteBootstrap(connection_factory).apply()

    if not app_config.telegram_token:
        logger.warning("No TELEGRAM token configured; bot startup skipped.")
        return

    bot = Bot(token=app_config.telegram_token)
    dispatcher = Dispatcher()
    acl_service = AclService(SqlitePrincipalTagRepository(connection_factory))
    AclBootstrapService(acl_service).apply(app_config.bootstrap_grants)
    router = Router()
    router.message.register(
        _build_start_handler(
            acl_service=acl_service,
            command_descriptors=command_descriptors,
        ),
        CommandStart(),
    )
    dispatcher.include_router(router)
    first_descriptor = command_descriptors[0]
    command_catalog = CommandCatalog(
        allowed_units=frozenset(app_config.allowed_units),
        allowed_zones=frozenset(app_config.allowed_zones),
    )
    rpz_service = RpzService(
        repository=SqliteRpzRuleRepository(connection_factory),
        command_catalog=command_catalog,
        command_runner=AsyncSubprocessRunner(),
        default_zone=app_config.allowed_zones[0] if app_config.allowed_zones else "",
    )
    command_pipeline = CommandCatalogBootstrap(
        descriptors=command_descriptors,
        definitions=command_definitions,
    ).build_pipeline(
        acl_service=acl_service,
        audit_service=PersistentAuditService(SqliteAuditRepository(connection_factory)),
        allowed_units=app_config.allowed_units,
        allowed_zones=app_config.allowed_zones,
        rpz_service=rpz_service,
    )
    request_factory = CommandRequestFactory(
        command_registry=command_pipeline.command_registry,
        token_parser=CommandTokenParser(),
    )
    telegram_gateway = TelegramCommandGateway(
        request_factory=request_factory,
        command_pipeline=command_pipeline,
    )
    controller = TelegramCommandController(
        gateway=telegram_gateway,
        callback_gateway=TelegramCallbackGateway(
            request_factory=CallbackRequestFactory(
                command_registry=command_pipeline.command_registry,
                token_parser=CommandTokenParser(),
            ),
            command_pipeline=command_pipeline,
        ),
        presenter=CommandPresenter(),
    )
    command_router = build_command_router(
        TelegramUpdateHandler(controller=controller),
        message_middlewares=(
            PrincipalResolverMiddleware(),
            CommandRequestBuildMiddleware(request_factory=request_factory),
            AccessLogMiddleware(),
        ),
    )
    dispatcher.include_router(command_router)
    _ = await controller.handle_text(
        principal_id=0,
        text=f"/{first_descriptor.name}",
    )

    stop_event = asyncio.Event()

    def _stop_signal_handler() -> None:
        logger.warning("Shutdown signal received, stopping bot process.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, _stop_signal_handler)
    loop.add_signal_handler(signal.SIGTERM, _stop_signal_handler)

    polling = asyncio.create_task(dispatcher.start_polling(bot))
    await stop_event.wait()
    polling.cancel()
    await bot.session.close()


def main() -> None:
    """Synchronous launcher with clean interruption.

    Returns:
        None
    """

    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Interrupted by user.")


if __name__ == "__main__":
    main()
