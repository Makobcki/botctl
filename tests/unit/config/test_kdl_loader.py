"""Unit tests for KDL loader adapter."""

from pathlib import Path

import pytest

from serverbot.domain.errors import DomainError
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_kdl_loader_parses_valid_file(tmp_path: Path) -> None:
    """KDL loader should produce typed config from valid input.

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

    result = KdlConfigLoader().load(str(config_file))

    assert result.telegram_token == "token"
    assert result.alert_chat_id == 10
    assert result.db_path == "/tmp/serverbot.db"
    assert result.allowed_units == ("bind9.service",)
    assert result.command_descriptors[0].name == "status"
    assert result.alert_checks[0].name == "health"


def test_kdl_loader_rejects_non_kdl_extension(tmp_path: Path) -> None:
    """KDL loader should reject files without `.kdl` extension.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.

    Raises:
        None.
    """

    config_file = tmp_path / "serverbot.txt"
    config_file.write_text("telegram_token \"token\"", encoding="utf-8")

    with pytest.raises(DomainError):
        KdlConfigLoader().load(str(config_file))
