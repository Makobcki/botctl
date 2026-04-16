"""Unit tests for worker checker factory foundation."""

import asyncio

from serverbot.domain.alerts import AlertCheckDescriptor
from serverbot.workers.checker_factory import CheckerFactory


def test_checker_factory_ignores_disabled_descriptors() -> None:
    """Factory should create checkers only for enabled descriptors.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    checker = CheckerFactory().create(
        (
            AlertCheckDescriptor(name="a", check_type="placeholder", interval_seconds=30, enabled=True),
            AlertCheckDescriptor(name="b", check_type="placeholder", interval_seconds=30, enabled=False),
        )
    )

    events = asyncio.run(checker.collect())

    assert events == []
