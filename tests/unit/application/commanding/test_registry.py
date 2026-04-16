"""Unit tests for command registry."""

from dataclasses import dataclass

import pytest

from serverbot.application.commanding.registry import CommandRegistry
from serverbot.domain.commanding.models import CommandDescriptor, CommandRequest, CommandResponse
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class StaticHandler:
    """Simple test handler returning static successful response.

    Args:
        message: Response message.
    """

    message: str

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Return static success response.

        Args:
            request: Incoming command request.

        Returns:
            Successful static response.

        Raises:
            None.
        """

        return CommandResponse(command_name=request.command_name, message=self.message, success=True)


def test_registry_rejects_duplicate_registration() -> None:
    """Registry should fail on duplicate command names.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    registry = CommandRegistry()
    descriptor = CommandDescriptor(name="status", required_tag="view.status", description="Server status")

    registry.register(descriptor=descriptor, handler=StaticHandler("ok"))

    with pytest.raises(DomainError):
        registry.register(descriptor=descriptor, handler=StaticHandler("ok"))


def test_registry_returns_registered_descriptor() -> None:
    """Registry should return command descriptor after registration.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    registry = CommandRegistry()
    descriptor = CommandDescriptor(name="status", required_tag="view.status", description="Server status")
    registry.register(descriptor=descriptor, handler=StaticHandler("ok"))

    result = registry.get("status")

    assert result.descriptor.name == "status"
