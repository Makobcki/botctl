"""Unit tests for Telegram update handler bridge."""

import asyncio
from dataclasses import dataclass

from serverbot.infrastructure.telegram_updates import TelegramUpdateHandler


@dataclass
class FakeUser:
    """Fake telegram user.

    Args:
        id: User id.
    """

    id: int


@dataclass
class FakeChat:
    """Fake telegram chat.

    Args:
        id: Chat id.
    """

    id: int


@dataclass
class FakeController:
    """Fake controller returning deterministic text.

    Args:
        text: Text to return.
    """

    text: str

    async def handle_text(self, principal_id: int, text: str) -> str:
        """Return deterministic text.

        Args:
            principal_id: Caller identifier.
            text: Incoming message.

        Returns:
            Response text.

        Raises:
            None.
        """

        _ = principal_id
        _ = text
        return self.text

    async def handle_callback(self, principal_id: int, data: str) -> str:
        """Return deterministic callback text.

        Args:
            principal_id: Caller identifier.
            data: Callback payload.

        Returns:
            Response text.

        Raises:
            None.
        """

        _ = principal_id
        _ = data
        return self.text


class FakeMessage:
    """Fake aiogram message object for handler tests."""

    def __init__(self, user_id: int, text: str) -> None:
        """Initialize fake message.

        Args:
            user_id: Fake user id.
            text: Message text.

        Returns:
            None.

        Raises:
            None.
        """

        self.from_user = FakeUser(user_id)
        self.chat = FakeChat(user_id)
        self.text = text
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        """Collect answer text.

        Args:
            text: Outgoing text.

        Returns:
            None.

        Raises:
            None.
        """

        self.answers.append(text)


class FakeCallbackQuery:
    """Fake callback query object for handler tests."""

    def __init__(self, user_id: int, data: str) -> None:
        """Initialize fake callback query.

        Args:
            user_id: Fake user id.
            data: Callback payload data.

        Returns:
            None.

        Raises:
            None.
        """

        self.from_user = FakeUser(user_id)
        self.data = data
        self.answers: list[str] = []

    async def answer(self, text: str, show_alert: bool) -> None:
        """Collect callback answer.

        Args:
            text: Outgoing text.
            show_alert: Alert flag.

        Returns:
            None.

        Raises:
            None.
        """

        _ = show_alert
        self.answers.append(text)


def test_update_handler_replies_with_controller_output() -> None:
    """Update handler should answer using controller output.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    handler = TelegramUpdateHandler(controller=FakeController(text="ok"))
    message = FakeMessage(user_id=42, text="/status")

    asyncio.run(handler.on_command_message(message))

    assert message.answers == ["ok"]


def test_update_handler_replies_to_callback_output() -> None:
    """Update handler should answer callback using controller output.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    handler = TelegramUpdateHandler(controller=FakeController(text="ok"))
    callback_query = FakeCallbackQuery(user_id=42, data="cmd:status")

    asyncio.run(handler.on_command_callback(callback_query))

    assert callback_query.answers == ["ok"]
