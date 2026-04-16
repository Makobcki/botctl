"""Unit tests for command presenter."""

from serverbot.application.commanding.presenter import CommandPresenter
from serverbot.domain.commanding.models import CommandResponse
from serverbot.domain.errors import DomainError


def test_presenter_renders_domain_error() -> None:
    """Presenter should include code and message for domain errors.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    text = CommandPresenter().present_domain_error(DomainError("invalid", "ERR_CODE"))

    assert text == "ERR_CODE: invalid"


def test_presenter_renders_success_message() -> None:
    """Presenter should return success message payload as is.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    response = CommandResponse(command_name="status", message="ok", success=True)

    text = CommandPresenter().present_success(response)

    assert text == "ok"
