"""Unit tests for ACL policy service."""

from serverbot.application.services import PolicyService
from serverbot.domain.models import CommandPolicy, Principal


def test_is_allowed_returns_true_for_matching_tag() -> None:
    """Policy returns True when principal contains required tag."""

    service = PolicyService(
        policies={"status": CommandPolicy(command_name="status", required_tag="view.status")}
    )
    principal = Principal(telegram_id=1, tags=frozenset({"view.status"}))

    assert service.is_allowed(principal, "status") is True


def test_is_allowed_returns_false_for_unknown_command() -> None:
    """Policy returns False when command policy does not exist."""

    service = PolicyService(policies={})
    principal = Principal(telegram_id=1, tags=frozenset({"view.status"}))

    assert service.is_allowed(principal, "status") is False
