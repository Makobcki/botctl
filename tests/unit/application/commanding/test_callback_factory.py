"""Unit tests for callback request factory."""

import pytest

from serverbot.application.commanding.callback_factory import CallbackRequestFactory
from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.token_parser import CommandTokenParser
from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
from serverbot.domain.errors import DomainError


def _registry() -> CommandRegistry:
    """Build command registry for callback tests.

    Args:
        None.

    Returns:
        Configured command registry.

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


def test_callback_factory_parses_command_and_args() -> None:
    """Factory should parse callback command and argument tokens.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    factory = CallbackRequestFactory(command_registry=_registry(), token_parser=CommandTokenParser())

    request = factory.from_callback_data(principal_id=7, data="cmd:logs lines=50")

    assert request.command_name == "logs"
    assert request.arguments["lines"] == "50"


def test_callback_factory_rejects_invalid_prefix() -> None:
    """Factory should fail for callback without cmd prefix.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    factory = CallbackRequestFactory(command_registry=_registry(), token_parser=CommandTokenParser())

    with pytest.raises(DomainError):
        factory.from_callback_data(principal_id=7, data="status")
