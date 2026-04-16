"""Unit tests for command argument validator."""

import pytest

from serverbot.application.commanding.validation import CommandArgumentValidator
from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
from serverbot.domain.errors import DomainError


def test_validator_rejects_missing_required_argument() -> None:
    """Validator should reject missing required argument.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    descriptor = CommandDescriptor(
        name="logs",
        required_tag="view.logs",
        description="Read logs",
        arguments=(
            CommandArgumentDescriptor(name="lines", value_type="int", required=True),
        ),
    )

    with pytest.raises(DomainError):
        CommandArgumentValidator().validate(descriptor, {})


def test_validator_accepts_valid_integer_argument() -> None:
    """Validator should accept integer argument encoded as string.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    descriptor = CommandDescriptor(
        name="logs",
        required_tag="view.logs",
        description="Read logs",
        arguments=(
            CommandArgumentDescriptor(name="lines", value_type="int", required=False),
        ),
    )

    CommandArgumentValidator().validate(descriptor, {"lines": "100"})
