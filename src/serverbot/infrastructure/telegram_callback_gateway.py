"""Callback payload gateway bridging callback data and command pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.callback_factory import CallbackRequestFactory
from serverbot.application.commanding.pipeline import CommandPipeline
from serverbot.domain.commanding.models import CommandResponse


@dataclass(frozen=True)
class TelegramCallbackGateway:
    """Adapter bridging callback payload and command pipeline.

    Args:
        request_factory: Callback request factory.
        command_pipeline: Command pipeline dependency.
    """

    request_factory: CallbackRequestFactory
    command_pipeline: CommandPipeline

    async def handle_callback(self, principal_id: int, data: str) -> CommandResponse:
        """Parse callback data and dispatch command pipeline.

        Args:
            principal_id: Telegram principal identifier.
            data: Callback payload.

        Returns:
            Command response from pipeline.

        Raises:
            Exception: Propagates parse and pipeline errors.
        """

        request = self.request_factory.from_callback_data(principal_id=principal_id, data=data)
        return await self.command_pipeline.dispatch(request)
