"""Controller that centralizes Telegram text command handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.application.commanding.presenter import CommandPresenter
from serverbot.infrastructure.telegram_callback_gateway import TelegramCallbackGateway
from serverbot.infrastructure.telegram_parser import TelegramCommandGateway
from serverbot.domain.errors import DomainError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramCommandController:
    """Controller handling Telegram text and formatting responses.

    Args:
        gateway: Text-to-pipeline gateway.
        callback_gateway: Callback-to-pipeline gateway.
        presenter: Response presenter.
    """

    gateway: TelegramCommandGateway
    callback_gateway: TelegramCallbackGateway
    presenter: CommandPresenter

    async def handle_text(self, principal_id: int, text: str) -> str:
        """Handle Telegram text command and return final response text.

        Args:
            principal_id: Telegram principal identifier.
            text: Raw Telegram message text.

        Returns:
            Final message text for user.

        Raises:
            None.
        """

        try:
            response = await self.gateway.handle_text(principal_id=principal_id, text=text)
            return self.presenter.present_success(response)
        except DomainError as error:
            logger.warning("Domain error while handling command: %s", error)
            return self.presenter.present_domain_error(error)
        except Exception:
            logger.exception("Unexpected error while handling command.")
            return self.presenter.present_internal_error()

    async def handle_callback(self, principal_id: int, data: str) -> str:
        """Handle callback payload and return final response text.

        Args:
            principal_id: Telegram principal identifier.
            data: Callback payload.

        Returns:
            Final message text for callback response.

        Raises:
            None.
        """

        try:
            response = await self.callback_gateway.handle_callback(principal_id=principal_id, data=data)
            return self.presenter.present_success(response)
        except DomainError as error:
            logger.warning("Domain error while handling callback: %s", error)
            return self.presenter.present_domain_error(error)
        except Exception:
            logger.exception("Unexpected error while handling callback.")
            return self.presenter.present_internal_error()
