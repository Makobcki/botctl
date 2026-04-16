"""Telegram text parsing adapter for command pipeline integration."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.application.commanding.pipeline import CommandPipeline
from serverbot.domain.commanding.models import CommandResponse


@dataclass(frozen=True)
class TelegramCommandGateway:
    """Adapter bridging Telegram text and command pipeline.

    Args:
        request_factory: Factory producing structured command requests.
        command_pipeline: Command processing pipeline.
    """

    request_factory: CommandRequestFactory
    command_pipeline: CommandPipeline

    async def handle_text(self, principal_id: int, text: str) -> CommandResponse:
        """Parse Telegram command text and dispatch command pipeline.

        Args:
            principal_id: Telegram principal identifier.
            text: Raw Telegram message text.

        Returns:
            Command response from pipeline.

        Raises:
            Exception: Propagates parsing and pipeline domain errors.
        """

        request = self.request_factory.from_telegram_text(principal_id=principal_id, text=text)
        return await self.command_pipeline.dispatch(request)
