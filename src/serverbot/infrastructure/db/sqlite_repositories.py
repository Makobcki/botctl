"""SQLite repository adapters for ACL and audit."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.repositories import AuditRecord, AuditRepository, PrincipalTagRepository


@dataclass(frozen=True)
class SqliteConnectionFactory:
    """Connection factory creating SQLite connections.

    Args:
        db_path: Filesystem path to SQLite database.
    """

    db_path: str

    def connect(self) -> sqlite3.Connection:
        """Create database connection and enforce foreign keys.

        Args:
            None.

        Returns:
            Open sqlite3 connection.

        Raises:
            sqlite3.Error: If opening the database fails.
        """

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


@dataclass(frozen=True)
class SqliteBootstrap:
    """Schema bootstrap helper for SQLite repositories.

    Args:
        connection_factory: Connection factory dependency.
    """

    connection_factory: SqliteConnectionFactory

    def apply(self) -> None:
        """Create required tables if they do not exist.

        Args:
            None.

        Returns:
            None.

        Raises:
            sqlite3.Error: If schema creation fails.
        """

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS principal_tags (
                    principal_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (principal_id, tag)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    principal_id INTEGER NOT NULL,
                    command_name TEXT NOT NULL,
                    success INTEGER NOT NULL
                )
                """
            )


@dataclass(frozen=True)
class SqlitePrincipalTagRepository(PrincipalTagRepository):
    """SQLite adapter implementing principal tag repository contract.

    Args:
        connection_factory: Connection factory dependency.
    """

    connection_factory: SqliteConnectionFactory

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Read all tags for principal.

        Args:
            principal_id: Telegram principal identifier.

        Returns:
            Immutable set of tags.

        Raises:
            sqlite3.Error: If query execution fails.
        """

        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                "SELECT tag FROM principal_tags WHERE principal_id = ? ORDER BY tag",
                (principal_id,),
            ).fetchall()
        return frozenset(row[0] for row in rows)

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Replace principal tags atomically.

        Args:
            principal_id: Telegram principal identifier.
            tags: Desired immutable tag set.

        Returns:
            None.

        Raises:
            sqlite3.Error: If write transaction fails.
        """

        with self.connection_factory.connect() as connection:
            connection.execute("DELETE FROM principal_tags WHERE principal_id = ?", (principal_id,))
            connection.executemany(
                "INSERT INTO principal_tags(principal_id, tag) VALUES(?, ?)",
                [(principal_id, tag) for tag in sorted(tags)],
            )


@dataclass(frozen=True)
class SqliteAuditRepository(AuditRepository):
    """SQLite adapter implementing audit repository contract.

    Args:
        connection_factory: Connection factory dependency.
    """

    connection_factory: SqliteConnectionFactory

    def append(self, record: AuditRecord) -> None:
        """Persist one audit row.

        Args:
            record: Structured audit payload.

        Returns:
            None.

        Raises:
            sqlite3.Error: If write fails.
        """

        with self.connection_factory.connect() as connection:
            connection.execute(
                "INSERT INTO audit_log(principal_id, command_name, success) VALUES(?, ?, ?)",
                (record.principal_id, record.command_name, int(record.success)),
            )

    def list_recent(self, limit: int) -> list[AuditRecord]:
        """Fetch recent audit records.

        Args:
            limit: Maximum number of records.

        Returns:
            List of newest records first.

        Raises:
            sqlite3.Error: If read fails.
        """

        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT principal_id, command_name, success
                FROM audit_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [AuditRecord(principal_id=row[0], command_name=row[1], success=bool(row[2])) for row in rows]
