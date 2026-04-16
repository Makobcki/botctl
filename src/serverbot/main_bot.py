"""Telegram bot process entrypoint."""

from __future__ import annotations

import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from serverbot.application.config_service import ConfigService
from serverbot.application.services import AuditService, PolicyService
from serverbot.application.use_cases import ExecuteCommandUseCase
from serverbot.config.logging import configure_logging
from serverbot.config.settings import RuntimeOptions
from serverbot.domain.models import CommandPolicy, Principal
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader

logger = logging.getLogger(__name__)


async def _on_start(message: Message) -> None:
    """Handle /start command.

    Args:
        message: Incoming Telegram message.

    Returns:
        None
    """

    await message.answer("serverbot is running")


async def run_bot() -> None:
    """Run telegram polling and graceful shutdown.

    Returns:
        None
    """

    runtime_options = RuntimeOptions()
    app_config = ConfigService(KdlConfigLoader()).load(runtime_options.config_path)
    configure_logging(app_config.verbose)

    if not app_config.telegram_token:
        logger.warning("No TELEGRAM token configured; bot startup skipped.")
        return

    bot = Bot(token=app_config.telegram_token)
    dispatcher = Dispatcher()
    router = Router()
    router.message.register(_on_start, CommandStart())
    dispatcher.include_router(router)

    policies = {
        "status": CommandPolicy(command_name="status", required_tag="view.status"),
    }
    use_case = ExecuteCommandUseCase(PolicyService(policies), AuditService())
    _ = await use_case.execute(Principal(telegram_id=0, tags=frozenset({"view.status"})), "status")

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
