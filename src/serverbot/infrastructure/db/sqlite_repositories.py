"""SQLite repository adapters for ACL and audit."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.repositories import (
    AuditRecord,
    AuditRepository,
    PrincipalTagRepository,
    RpzRuleRecord,
    RpzRuleRepository,
)


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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rpz_rules (
                    zone TEXT NOT NULL,
                    qname TEXT NOT NULL,
                    policy TEXT NOT NULL,
                    value TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (zone, qname)
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

    def has_principals(self) -> bool:
        """Check if at least one ACL principal exists.

        Args:
            None.

        Returns:
            True when repository contains one or more principals.

        Raises:
            sqlite3.Error: If query fails.
        """

        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM principal_tags LIMIT 1"
            ).fetchone()
        return row is not None


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


@dataclass(frozen=True)
class SqliteRpzRuleRepository(RpzRuleRepository):
    """SQLite adapter implementing RPZ rule repository.

    Args:
        connection_factory: Connection factory dependency.
    """

    connection_factory: SqliteConnectionFactory

    def upsert(self, record: RpzRuleRecord) -> None:
        """Insert or replace RPZ rule.

        Args:
            record: RPZ record payload.

        Returns:
            None.
        """

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO rpz_rules(zone, qname, policy, value)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(zone, qname) DO UPDATE SET
                    policy = excluded.policy,
                    value = excluded.value
                """,
                (record.zone, record.qname, record.policy, record.value),
            )

    def delete(self, zone: str, qname: str) -> bool:
        """Delete RPZ rule by key.

        Args:
            zone: Zone name.
            qname: Rule qname.

        Returns:
            True if any row was deleted.
        """

        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM rpz_rules WHERE zone = ? AND qname = ?",
                (zone, qname),
            )
        return cursor.rowcount > 0

    def list_rules(self, zone: str | None = None) -> list[RpzRuleRecord]:
        """List RPZ rules optionally filtered by zone.

        Args:
            zone: Optional zone filter.

        Returns:
            Sorted list of RPZ records.
        """

        with self.connection_factory.connect() as connection:
            if zone is None:
                rows = connection.execute(
                    "SELECT zone, qname, policy, value FROM rpz_rules ORDER BY zone, qname"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT zone, qname, policy, value
                    FROM rpz_rules
                    WHERE zone = ?
                    ORDER BY qname
                    """,
                    (zone,),
                ).fetchall()
        return [RpzRuleRecord(zone=row[0], qname=row[1], policy=row[2], value=row[3]) for row in rows]

    def find_rules(self, query: str, zone: str | None = None) -> list[RpzRuleRecord]:
        """Find RPZ rules by qname query.

        Args:
            query: Query substring.
            zone: Optional zone filter.

        Returns:
            Matching records sorted by zone/qname.
        """

        pattern = f"%{query}%"
        with self.connection_factory.connect() as connection:
            if zone is None:
                rows = connection.execute(
                    """
                    SELECT zone, qname, policy, value
                    FROM rpz_rules
                    WHERE qname LIKE ?
                    ORDER BY zone, qname
                    """,
                    (pattern,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT zone, qname, policy, value
                    FROM rpz_rules
                    WHERE zone = ? AND qname LIKE ?
                    ORDER BY qname
                    """,
                    (zone, pattern),
                ).fetchall()
        return [RpzRuleRecord(zone=row[0], qname=row[1], policy=row[2], value=row[3]) for row in rows]
