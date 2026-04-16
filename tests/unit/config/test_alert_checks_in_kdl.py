"""Unit tests for alert check declarations in KDL."""

from pathlib import Path

import pytest

from serverbot.domain.errors import DomainError
from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_kdl_loader_rejects_invalid_alert_check_declaration(tmp_path: Path) -> None:
    """Loader should fail on invalid alert_check declaration syntax.

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
                'alert_check "health" type="placeholder" interval=abc enabled=true',
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(DomainError):
        KdlConfigLoader().load(str(config_file))
