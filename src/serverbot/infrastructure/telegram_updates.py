"""Aiogram update handling bridge for command controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from serverbot.infrastructure.telegram_controller import TelegramCommandController


@dataclass(frozen=True)
class TelegramUpdateHandler:
    """Handles Telegram updates and delegates to command controller.

    Args:
        controller: Command controller dependency.
    """

    controller: TelegramCommandController

    async def on_command_message(self, message: Any) -> None:
        """Process command-like Telegram message and answer with text.

        Args:
            message: Incoming Telegram message.

        Returns:
            None.

        Raises:
            None.
        """

        principal_id = message.from_user.id if message.from_user else message.chat.id
        text = message.text or ""
        response_text = await self.controller.handle_text(principal_id=principal_id, text=text)
        await message.answer(response_text)

    async def on_command_callback(self, callback_query: Any) -> None:
        """Process callback command payload and answer through controller.

        Args:
            callback_query: Incoming callback query object.

        Returns:
            None.

        Raises:
            None.
        """

        principal_id = callback_query.from_user.id
        data = callback_query.data or ""
        response_text = await self.controller.handle_callback(principal_id=principal_id, data=data)
        await callback_query.answer(response_text, show_alert=False)


def build_command_router(
    handler: TelegramUpdateHandler,
    message_middlewares: tuple[Any, ...] = (),
) -> Any:
    """Build aiogram router for command messages.

    Args:
        handler: Update handler instance.
        message_middlewares: Message middlewares to attach.

    Returns:
        Configured aiogram router.

    Raises:
        None.
    """

    from aiogram import F, Router

    router = Router()
    router.message.register(handler.on_command_message, F.text.startswith("/"))
    for middleware in message_middlewares:
        router.message.outer_middleware(middleware)
    router.callback_query.register(handler.on_command_callback, F.data.startswith("cmd:"))
    return router
