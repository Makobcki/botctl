"""Unit tests for Telegram command controller."""

import asyncio
from dataclasses import dataclass

from serverbot.application.commanding.presenter import CommandPresenter
from serverbot.domain.commanding.models import CommandResponse
from serverbot.domain.errors import DomainError
from serverbot.infrastructure.telegram_controller import TelegramCommandController


@dataclass
class SuccessGateway:
    """Gateway stub returning successful response.

    Args:
        None.
    """

    async def handle_text(self, principal_id: int, text: str) -> CommandResponse:
        """Return static success response.

        Args:
            principal_id: Telegram principal identifier.
            text: Raw input text.

        Returns:
            Successful command response.

        Raises:
            None.
        """

        _ = principal_id
        _ = text
        return CommandResponse(command_name="status", message="ok", success=True)


@dataclass
class DomainErrorGateway:
    """Gateway stub raising domain error.

    Args:
        None.
    """

    async def handle_text(self, principal_id: int, text: str) -> CommandResponse:
        """Raise domain error.

        Args:
            principal_id: Telegram principal identifier.
            text: Raw input text.

        Returns:
            Never returns.

        Raises:
            DomainError: Always raised.
        """

        _ = principal_id
        _ = text
        raise DomainError("bad command", "COMMAND_BAD")


@dataclass
class CallbackSuccessGateway:
    """Callback gateway stub returning successful response."""

    async def handle_callback(self, principal_id: int, data: str) -> CommandResponse:
        """Return static callback response.

        Args:
            principal_id: Telegram principal identifier.
            data: Callback payload.

        Returns:
            Successful command response.

        Raises:
            None.
        """

        _ = principal_id
        _ = data
        return CommandResponse(command_name="status", message="ok", success=True)


def test_controller_returns_presented_success() -> None:
    """Controller should return presenter success rendering for successful gateway result.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    controller = TelegramCommandController(
        gateway=SuccessGateway(),
        callback_gateway=CallbackSuccessGateway(),
        presenter=CommandPresenter(),
    )

    text = asyncio.run(controller.handle_text(1, "/status"))

    assert text == "ok"


def test_controller_returns_presented_domain_error() -> None:
    """Controller should map domain errors through presenter.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    controller = TelegramCommandController(
        gateway=DomainErrorGateway(),
        callback_gateway=CallbackSuccessGateway(),
        presenter=CommandPresenter(),
    )

    text = asyncio.run(controller.handle_text(1, "/status"))

    assert text == "COMMAND_BAD: bad command"


def test_controller_returns_presented_callback_success() -> None:
    """Controller should map callback gateway response through presenter.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    controller = TelegramCommandController(
        gateway=SuccessGateway(),
        callback_gateway=CallbackSuccessGateway(),
        presenter=CommandPresenter(),
    )

    text = asyncio.run(controller.handle_callback(1, "cmd:status"))

    assert text == "ok"
