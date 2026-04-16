"""Unit tests validating command declarations in KDL config."""

from pathlib import Path

import pytest

from serverbot.domain.errors import DomainError
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_kdl_loader_requires_at_least_one_command(tmp_path: Path) -> None:
    """Loader should reject config without command declarations.

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

    with pytest.raises(DomainError):
        KdlConfigLoader().load(str(config_file))


def test_kdl_loader_parses_command_declaration(tmp_path: Path) -> None:
    """Loader should parse command metadata from KDL declarations.

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
                'command_arg "status" name="details" type="str" required=false',
                'alert_check "health" type="placeholder" interval=30 enabled=true',
            ]
        ),
        encoding="utf-8",
    )

    result = KdlConfigLoader().load(str(config_file))

    assert result.command_descriptors[0].required_tag == "view.status"
    assert result.command_descriptors[0].arguments[0].name == "details"
    assert result.alert_checks[0].check_type == "placeholder"
