"""Validation tests for bundled example KDL configuration."""

from pathlib import Path

from serverbot.infrastructure.config.kdl_loader import KdlConfigLoader


def test_example_kdl_is_valid_and_parsable() -> None:
    """Bundled example KDL should parse into non-empty structures.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    example_path = Path("config/example.kdl")

    result = KdlConfigLoader().load(str(example_path))

    assert len(result.command_descriptors) >= 3
    assert len(result.alert_checks) >= 1
    assert len(result.bootstrap_grants) >= 1
