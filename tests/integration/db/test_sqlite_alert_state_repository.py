"""Integration tests for SQLite alert state repository."""

from pathlib import Path

from serverbot.domain.alerts import AlertState
from serverbot.infrastructure.db.sqlite_alert_state_repository import (
    SqliteAlertStateBootstrap,
    SqliteAlertStateRepository,
)
from serverbot.infrastructure.db.sqlite_repositories import SqliteConnectionFactory


def test_sqlite_alert_state_roundtrip(tmp_path: Path) -> None:
    """Repository should persist and read alert state by key.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    factory = SqliteConnectionFactory(str(tmp_path / "alert.db"))
    SqliteAlertStateBootstrap(factory).apply()
    repository = SqliteAlertStateRepository(factory)

    repository.set(AlertState(key="bind9_down", is_firing=True))

    result = repository.get("bind9_down")

    assert result is not None
    assert result.is_firing is True
