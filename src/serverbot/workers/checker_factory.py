"""Factory for creating configured worker checkers from KDL descriptors."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.worker_alerts import AlertChecker
from serverbot.domain.alerts import AlertCheckDescriptor, AlertEvent


@dataclass(frozen=True)
class PlaceholderConfiguredChecker(AlertChecker):
    """Configured checker placeholder that currently emits no events.

    Args:
        descriptor: Alert checker descriptor.
    """

    descriptor: AlertCheckDescriptor

    async def collect(self) -> list[AlertEvent]:
        """Collect no events for placeholder checker.

        Args:
            None.

        Returns:
            Empty list of events.

        Raises:
            None.
        """

        return []


@dataclass(frozen=True)
class CompositeChecker(AlertChecker):
    """Aggregate multiple checkers into one logical checker.

    Args:
        checkers: Child checkers.
    """

    checkers: tuple[AlertChecker, ...]

    async def collect(self) -> list[AlertEvent]:
        """Collect events from all child checkers.

        Args:
            None.

        Returns:
            Combined list of alert events.

        Raises:
            Exception: Propagates child checker failures.
        """

        events: list[AlertEvent] = []
        for checker in self.checkers:
            events.extend(await checker.collect())
        return events


@dataclass(frozen=True)
class CheckerFactory:
    """Builds composite checker graph from configured descriptors.

    Args:
        None.
    """

    def create(self, descriptors: tuple[AlertCheckDescriptor, ...]) -> AlertChecker:
        """Create checker collection based on descriptors.

        Args:
            descriptors: Configured checker descriptors.

        Returns:
            Composite checker with configured placeholders.

        Raises:
            None.
        """

        checkers = tuple(
            PlaceholderConfiguredChecker(descriptor=descriptor)
            for descriptor in descriptors
            if descriptor.enabled
        )
        return CompositeChecker(checkers=checkers)
