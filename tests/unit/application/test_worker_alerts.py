"""Unit tests for worker alert deduplication engine."""

from dataclasses import dataclass
import asyncio

from serverbot.application.worker_alerts import AlertEngine
from serverbot.domain.alerts import AlertEvent, AlertState


@dataclass
class InMemoryStateRepository:
    """In-memory repository for alert states.

    Args:
        state: Mutable state mapping.
    """

    state: dict[str, AlertState]

    def get(self, key: str) -> AlertState | None:
        """Get state by key.

        Args:
            key: Alert key.

        Returns:
            Found state or None.

        Raises:
            None.
        """

        return self.state.get(key)

    def set(self, state: AlertState) -> None:
        """Store state by key.

        Args:
            state: Alert state payload.

        Returns:
            None.

        Raises:
            None.
        """

        self.state[state.key] = state


@dataclass
class InMemoryNotifier:
    """In-memory notifier collecting sent events.

    Args:
        sent: Collected events.
    """

    sent: list[AlertEvent]

    async def notify(self, event: AlertEvent) -> None:
        """Collect sent event.

        Args:
            event: Alert event payload.

        Returns:
            None.

        Raises:
            None.
        """

        self.sent.append(event)


def test_alert_engine_sends_only_transitions() -> None:
    """Engine should notify on firing and recovery transitions only.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    state_repository = InMemoryStateRepository(state={})
    notifier = InMemoryNotifier(sent=[])
    engine = AlertEngine(state_repository=state_repository, notifier=notifier)

    event = AlertEvent(key="bind9_down", title="BIND down", details="inactive", is_firing=True)
    sent_count_first = asyncio.run(engine.process([event]))
    sent_count_second = asyncio.run(engine.process([event]))
    recovery = AlertEvent(key="bind9_down", title="BIND up", details="active", is_firing=False)
    sent_count_third = asyncio.run(engine.process([recovery]))

    assert sent_count_first == 1
    assert sent_count_second == 0
    assert sent_count_third == 1
    assert len(notifier.sent) == 2
