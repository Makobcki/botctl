"""Validation tests for bundled command KDL configuration."""

from pathlib import Path

from serverbot.infrastructure.config.command_kdl_loader import CommandKdlLoader


def test_example_kdl_is_valid_and_parsable() -> None:
    """Bundled command KDL should parse into non-empty descriptors.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    example_path = Path("commands/example.kdl")

    result = CommandKdlLoader().load(str(example_path))

    assert len(result) >= 3
