"""Unit tests for command-specific KDL loader."""

from pathlib import Path

from serverbot.infrastructure.config.command_kdl_loader import CommandKdlLoader


def test_command_kdl_loader_parses_command_help_and_categories(tmp_path: Path) -> None:
    """Loader should parse command help text and categories.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """

    config_file = tmp_path / "commands.kdl"
    config_file.write_text(
        "\n".join(
            [
                'name "test"',
                'description "test command"',
                'category = ["docs", "docker"]',
                "execute {",
                '    command "echo ok"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = CommandKdlLoader().load(str(config_file))

    assert result[0].name == "test"
    assert result[0].help == "test command"
    assert result[0].categories == ("docs", "docker")
