"""Validation tests for bundled command KDL configurations."""

from pathlib import Path

from serverbot.infrastructure.config.command_kdl_loader import CommandKdlLoader


def test_production_command_directory_is_valid_and_parsable() -> None:
    """Production command KDL directory should parse into expected descriptors.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    production_path = Path("commands")

    result = CommandKdlLoader().load(str(production_path))

    descriptor_names = {descriptor.name for descriptor in result}
    assert {"status", "docker", "services", "logs", "bind", "rpz", "acl", "audit", "whoami", "exec"} <= descriptor_names


def test_example_kdl_remains_valid_for_docs() -> None:
    """Example command KDL should stay parseable as lightweight sample.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    example_path = Path("commands/example.kdl")
    result = CommandKdlLoader().load(str(example_path))
    assert len(result) == 1
