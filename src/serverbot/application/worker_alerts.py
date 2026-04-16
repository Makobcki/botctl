"""Worker alert orchestration without concrete monitor actions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from serverbot.domain.alerts import AlertEvent, AlertState

logger = logging.getLogger(__name__)


class AlertStateRepository(Protocol):
    """Storage contract for alert deduplication states."""

    def get(self, key: str) -> AlertState | None:
        """Read current state by key.

        Args:
            key: Alert key.

        Returns:
            Current state or None.

        Raises:
            Exception: Storage adapter errors.
        """

    def set(self, state: AlertState) -> None:
        """Persist state for key.

        Args:
            state: Alert state payload.

        Returns:
            None.

        Raises:
            Exception: Storage adapter errors.
        """


class AlertNotifier(Protocol):
    """Outgoing notification contract for alert messages."""

    async def notify(self, event: AlertEvent) -> None:
        """Send one alert event.

        Args:
            event: Alert event payload.

        Returns:
            None.

        Raises:
            Exception: Transport adapter errors.
        """


class AlertChecker(Protocol):
    """Monitor checker contract producing alert events."""

    async def collect(self) -> list[AlertEvent]:
        """Collect current monitor events.

        Args:
            None.

        Returns:
            List of current check events.

        Raises:
            Exception: Checker implementation errors.
        """


@dataclass(frozen=True)
class AlertEngine:
    """Deduplicating alert processor with persistence and notifications.

    Args:
        state_repository: Alert state repository.
        notifier: Alert notifier implementation.
    """

    state_repository: AlertStateRepository
    notifier: AlertNotifier

    async def process(self, events: list[AlertEvent]) -> int:
        """Process events and notify only state transitions.

        Args:
            events: Collected alert events.

        Returns:
            Number of notifications sent.

        Raises:
            Exception: Storage or notification failures.
        """

        sent_count = 0
        for event in events:
            if self._should_notify(event):
                await self.notifier.notify(event)
                self.state_repository.set(AlertState(key=event.key, is_firing=event.is_firing))
                sent_count += 1
                logger.info("Alert transition sent key=%s firing=%s", event.key, event.is_firing)
            else:
                logger.debug("Alert transition skipped key=%s firing=%s", event.key, event.is_firing)
        return sent_count

    def _should_notify(self, event: AlertEvent) -> bool:
        """Decide whether event changes persisted state.

        Args:
            event: Candidate alert event.

        Returns:
            True when event must be sent.

        Raises:
            None.
        """

        current_state = self.state_repository.get(event.key)
        if current_state is None:
            return event.is_firing
        return current_state.is_firing != event.is_firing


@dataclass(frozen=True)
class WorkerAlertLoop:
    """Polling loop runner for alert checkers.

    Args:
        checker: Alert checker implementation.
        engine: Alert engine implementation.
    """

    checker: AlertChecker
    engine: AlertEngine

    async def tick(self) -> int:
        """Run one poll cycle and return sent notifications count.

        Args:
            None.

        Returns:
            Number of notifications sent in this tick.

        Raises:
            Exception: Propagates checker or engine failures.
        """

        events = await self.checker.collect()
        return await self.engine.process(events)
