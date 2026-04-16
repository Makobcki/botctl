"""Application settings module."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeOptions:
    """Runtime options for process bootstrapping.

    Args:
        config_path: Path to KDL configuration file.
    """

    config_path: str = "config/serverbot.kdl"
