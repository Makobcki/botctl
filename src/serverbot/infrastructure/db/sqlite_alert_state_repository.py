"""SQLite adapter for persistent alert state deduplication."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.worker_alerts import AlertStateRepository
from serverbot.domain.alerts import AlertState
from serverbot.infrastructure.db.sqlite_repositories import SqliteConnectionFactory


@dataclass(frozen=True)
class SqliteAlertStateBootstrap:
    """Create alert state table in SQLite if needed.

    Args:
        connection_factory: SQLite connection factory.
    """

    connection_factory: SqliteConnectionFactory

    def apply(self) -> None:
        """Create alert state table.

        Args:
            None.

        Returns:
            None.

        Raises:
            Exception: SQLite operation failures.
        """

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_state (
                    alert_key TEXT PRIMARY KEY,
                    is_firing INTEGER NOT NULL
                )
                """
            )


@dataclass(frozen=True)
class SqliteAlertStateRepository(AlertStateRepository):
    """SQLite-backed alert state repository.

    Args:
        connection_factory: SQLite connection factory.
    """

    connection_factory: SqliteConnectionFactory

    def get(self, key: str) -> AlertState | None:
        """Fetch alert state by key.

        Args:
            key: Alert key.

        Returns:
            Alert state or None if missing.

        Raises:
            Exception: SQLite read failures.
        """

        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT alert_key, is_firing FROM alert_state WHERE alert_key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        return AlertState(key=row[0], is_firing=bool(row[1]))

    def set(self, state: AlertState) -> None:
        """Persist alert state by upsert.

        Args:
            state: Alert state payload.

        Returns:
            None.

        Raises:
            Exception: SQLite write failures.
        """

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO alert_state(alert_key, is_firing)
                VALUES(?, ?)
                ON CONFLICT(alert_key) DO UPDATE SET is_firing = excluded.is_firing
                """,
                (state.key, int(state.is_firing)),
            )
