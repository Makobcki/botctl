"""Unit tests for Telegram middleware foundations."""

import asyncio
from dataclasses import dataclass
from typing import Any

from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.infrastructure.telegram_middlewares import (
    AccessLogMiddleware,
    CommandRequestBuildMiddleware,
    PrincipalResolverMiddleware,
)


@dataclass
class FakeUser:
    """Fake user object.

    Args:
        id: Telegram user id.
    """

    id: int


@dataclass
class FakeMessage:
    """Fake message object for middleware tests.

    Args:
        user_id: Telegram user id.
        text: Message text.
    """

    user_id: int
    text: str

    @property
    def from_user(self) -> FakeUser:
        """Return fake user object.

        Args:
            None.

        Returns:
            Fake user.

        Raises:
            None.
        """

        return FakeUser(id=self.user_id)


def _registry() -> CommandRegistry:
    """Build command registry for middleware tests.

    Args:
        None.

    Returns:
        Command registry with `status` command.

    Raises:
        None.
    """

    registry = CommandRegistry()
    registry.register(
        descriptor=CommandDescriptor(
            name="status",
            required_tag="view.status",
            description="Show status",
        ),
        handler=PlaceholderHandler("ok"),
    )
    return registry


async def _final_handler(event: Any, data: dict[str, Any]) -> dict[str, Any]:
    """Return middleware context for assertions.

    Args:
        event: Event object.
        data: Middleware context.

    Returns:
        Context dictionary.

    Raises:
        None.
    """

    _ = event
    return data


def test_middlewares_build_principal_and_request_context() -> None:
    """Middlewares should enrich context with principal and request.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    event = FakeMessage(user_id=77, text="/status")
    resolver = PrincipalResolverMiddleware()
    builder = CommandRequestBuildMiddleware(
        request_factory=CommandRequestFactory(
            command_registry=_registry(),
            token_parser=CommandTokenParser(),
        )
    )
    logger_mw = AccessLogMiddleware()

    async def chain(ev: Any, data: dict[str, Any]) -> dict[str, Any]:
        """Compose middleware chain for tests.

        Args:
            ev: Event.
            data: Context.

        Returns:
            Final context.

        Raises:
            None.
        """

        return await resolver(
            lambda e1, d1: builder(lambda e2, d2: logger_mw(_final_handler, e2, d2), e1, d1),
            ev,
            data,
        )

    context = asyncio.run(chain(event, {}))

    assert context["principal_id"] == 77
    assert context["command_request"].command_name == "status"
