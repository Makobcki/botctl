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


def test_command_kdl_loader_reads_directory_and_skips_example(tmp_path: Path) -> None:
    """Loader should read all command files in directory except example.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        None.
    """

    main_file = tmp_path / "status.kdl"
    example_file = tmp_path / "example.kdl"
    main_file.write_text(
        "\n".join(
            [
                'name "status"',
                'description "status command"',
                "execute {",
                '    command "echo ok"',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    example_file.write_text(
        "\n".join(
            [
                'name "example"',
                'description "example command"',
                "execute {",
                '    command "echo sample"',
                "}",
            ]
        ),
        encoding="utf-8",
    )

    result = CommandKdlLoader().load(str(tmp_path))

    assert [item.name for item in result] == ["status"]
