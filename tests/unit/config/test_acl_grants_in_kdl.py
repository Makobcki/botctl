"""Unit tests for ACL grant declarations in KDL config."""

from pathlib import Path

from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_kdl_loader_parses_acl_grants(tmp_path: Path) -> None:
    """Loader should parse principal grant declarations.

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
                'alert_check "health" type="placeholder" interval=30 enabled=true',
                'principal_grant "user:1" tag="view.status"',
            ]
        ),
        encoding="utf-8",
    )

    result = KdlConfigLoader().load(str(config_file))

    assert result.bootstrap_grants[0].principal_id == 1
    assert result.bootstrap_grants[0].tag == "view.status"
