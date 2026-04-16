"""Unit tests validating runtime KDL excludes command declarations."""

from pathlib import Path

import pytest

from serverbot.domain.errors import DomainError
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_kdl_loader_allows_runtime_config_without_commands(tmp_path: Path) -> None:
    """Loader should parse runtime config without command declarations.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    config_file = tmp_path / "serverbot.kdl"
    config_file.write_text(
        '\n'.join(
            [
                'telegram_token "token"',
                'alert_chat_id 10',
                'verbose true',
                'worker_interval_seconds 42',
                'db_path "/tmp/serverbot.db"',
                'allowed_units ["bind9.service"]',
                'allowed_zones ["rpz.local"]',
            ]
        ),
        encoding="utf-8",
    )

    result = KdlConfigLoader().load(str(config_file))
    assert result.command_descriptors == tuple()


def test_kdl_loader_rejects_command_declarations_in_runtime_config(tmp_path: Path) -> None:
    """Loader should reject command metadata in runtime config.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    config_file = tmp_path / "serverbot.kdl"
    config_file.write_text(
        '\n'.join(
            [
                'telegram_token "token"',
                'alert_chat_id 10',
                'verbose true',
                'worker_interval_seconds 42',
                'db_path "/tmp/serverbot.db"',
                'allowed_units ["bind9.service"]',
                'allowed_zones ["rpz.local"]',
                'command "status" tag="view.status" description="Show status"',
                'alert_check "health" type="placeholder" interval=30 enabled=true',
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(DomainError):
        KdlConfigLoader().load(str(config_file))
