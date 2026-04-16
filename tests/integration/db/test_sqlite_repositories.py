"""Integration tests for SQLite repository adapters."""

from pathlib import Path

from serverbot.domain.repositories import AuditRecord
from serverbot.infrastructure.db.sqlite_repositories import (
    SqliteAuditRepository,
    SqliteBootstrap,
    SqliteConnectionFactory,
    SqlitePrincipalTagRepository,
)


def test_sqlite_principal_tags_roundtrip(tmp_path: Path) -> None:
    """Repository should persist and return principal tags.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "serverbot.db"))
    SqliteBootstrap(connection_factory).apply()
    repository = SqlitePrincipalTagRepository(connection_factory)

    repository.set_tags(1, frozenset({"view.status", "ops.bind"}))

    result = repository.get_tags(1)

    assert result == frozenset({"view.status", "ops.bind"})


def test_sqlite_audit_recent_order(tmp_path: Path) -> None:
    """Repository should return newest audit records first.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    connection_factory = SqliteConnectionFactory(str(tmp_path / "serverbot.db"))
    SqliteBootstrap(connection_factory).apply()
    repository = SqliteAuditRepository(connection_factory)

    repository.append(AuditRecord(principal_id=1, command_name="status", success=True))
    repository.append(AuditRecord(principal_id=2, command_name="logs", success=False))

    records = repository.list_recent(limit=2)

    assert [record.command_name for record in records] == ["logs", "status"]
