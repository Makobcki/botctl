"""Unit tests for Telegram command request factory."""

import pytest

from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.request_factory import CommandRequestFactory
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
from serverbot.domain.errors import DomainError


def _build_registry() -> CommandRegistry:
    """Create test command registry.

    Args:
        None.

    Returns:
        Registry with one command descriptor.

    Raises:
        None.
    """

    registry = CommandRegistry()
    registry.register(
        descriptor=CommandDescriptor(
            name="logs",
            required_tag="view.logs",
            description="Read logs",
            arguments=(
                CommandArgumentDescriptor(name="lines", value_type="int", required=False),
            ),
        ),
        handler=PlaceholderHandler("ok"),
    )
    return registry


def test_request_factory_parses_positional_argument() -> None:
    """Factory should map positional argument by descriptor order.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    request = CommandRequestFactory(_build_registry(), CommandTokenParser()).from_telegram_text(1, "/logs 100")

    assert request.command_name == "logs"
    assert request.arguments["lines"] == "100"


def test_request_factory_rejects_invalid_prefix() -> None:
    """Factory should fail for text without slash prefix.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    with pytest.raises(DomainError):
        CommandRequestFactory(_build_registry(), CommandTokenParser()).from_telegram_text(1, "logs 100")
