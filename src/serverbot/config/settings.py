"""Application settings module."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeOptions:
    """Runtime options for process bootstrapping.

    Args:
        config_path: Path to runtime KDL configuration file.
        command_config_path: Path to command-definition KDL file.
    """

    config_path: str = "config/serverbot.kdl"
    command_config_path: str = "commands"
