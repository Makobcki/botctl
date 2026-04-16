"""Middleware foundations for Telegram command update processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.domain.commanding.models import CommandRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrincipalResolverMiddleware:
    """Resolve principal id from Telegram event and store in context.

    Args:
        context_key: Key used to store principal id in middleware context.
    """

    context_key: str = "principal_id"

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Extract principal id and forward control to next middleware.

        Args:
            handler: Next middleware or endpoint handler.
            event: Incoming Telegram event.
            data: Mutable context dictionary.

        Returns:
            Result from next handler.

        Raises:
            Exception: Propagates downstream exceptions.
        """

        principal_id = event.from_user.id if event.from_user else event.chat.id
        data[self.context_key] = principal_id
        logger.debug("Resolved principal_id=%s", principal_id)
        return await handler(event, data)


@dataclass(frozen=True)
class CommandRequestBuildMiddleware:
    """Build command request from Telegram message text.

    Args:
        request_factory: Command request factory.
        request_key: Key used to store built command request.
    """

    request_factory: CommandRequestFactory
    request_key: str = "command_request"

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Build `CommandRequest` and forward context downstream.

        Args:
            handler: Next middleware or endpoint handler.
            event: Incoming Telegram event.
            data: Mutable context dictionary.

        Returns:
            Result from next handler.

        Raises:
            Exception: Propagates factory and downstream errors.
        """

        principal_id = data["principal_id"]
        text = event.text or ""
        command_request: CommandRequest = self.request_factory.from_telegram_text(
            principal_id=principal_id,
            text=text,
        )
        data[self.request_key] = command_request
        logger.debug("Built command request name=%s", command_request.command_name)
        return await handler(event, data)


@dataclass(frozen=True)
class AccessLogMiddleware:
    """Log incoming command metadata for observability.

    Args:
        None.
    """

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Emit structured access log and forward processing.

        Args:
            handler: Next middleware or endpoint handler.
            event: Incoming Telegram event.
            data: Mutable context dictionary.

        Returns:
            Result from next handler.

        Raises:
            Exception: Propagates downstream failures.
        """

        principal_id = data.get("principal_id", "unknown")
        text = event.text or ""
        logger.info("telegram access principal=%s text=%s", principal_id, text)
        return await handler(event, data)
