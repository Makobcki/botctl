"""Placeholder worker checkers before concrete monitoring actions are implemented."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.worker_alerts import AlertChecker
from serverbot.domain.alerts import AlertEvent


@dataclass(frozen=True)
class EmptyChecker(AlertChecker):
    """Checker producing no events for bootstrap stability.

    Args:
        None.
    """

    async def collect(self) -> list[AlertEvent]:
        """Collect no events.

        Args:
            None.

        Returns:
            Empty list.

        Raises:
            None.
        """

        return []
