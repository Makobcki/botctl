"""Unit tests for command catalog validations."""

import pytest

from serverbot.infrastructure.command_catalog import CommandCatalog, CommandValidationError


def test_journal_unit_builds_command() -> None:
    """Journal command is created for valid unit/lines arguments."""

    catalog = CommandCatalog(
        allowed_units=frozenset({"bind9.service"}),
        allowed_zones=frozenset({"rpz.local"}),
    )

    command = catalog.journal_unit("bind9.service", 10)

    assert command == ["journalctl", "--unit", "bind9.service", "-n", "10", "--no-pager"]


def test_bind_reload_rejects_unknown_zone() -> None:
    """Unknown zone should fail fast through validation error."""

    catalog = CommandCatalog(
        allowed_units=frozenset({"bind9.service"}),
        allowed_zones=frozenset({"rpz.local"}),
    )

    with pytest.raises(CommandValidationError):
        catalog.bind_reload("unknown.local")
