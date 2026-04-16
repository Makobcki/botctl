"""Configuration application service."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.domain.ports import AppConfig, ConfigLoader


@dataclass(frozen=True)
class ConfigService:
    """Service that loads configuration through adapter port.

    Args:
        config_loader: Loader implementation bound by DI.
    """

    config_loader: ConfigLoader

    def load(self, path: str) -> AppConfig:
        """Load and validate runtime configuration.

        Args:
            path: Path to configuration file.

        Returns:
            Immutable app configuration.

        Raises:
            Exception: Loader-specific parse errors.
        """

        return self.config_loader.load(path)
