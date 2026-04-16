"""Validated command templates for shell adapters."""

from __future__ import annotations

from dataclasses import dataclass


class CommandValidationError(ValueError):
    """Raised when arguments fail command allow-list validation."""


@dataclass(frozen=True)
class CommandCatalog:
    """Whitelisted command template registry."""

    allowed_units: frozenset[str]
    allowed_zones: frozenset[str]

    def journal_unit(self, unit: str, lines: int) -> list[str]:
        """Build a journalctl command from validated arguments.

        Args:
            unit: Systemd unit name.
            lines: Number of lines requested.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If unit or line count is not allowed.
        """

        if unit not in self.allowed_units:
            raise CommandValidationError(f"Unsupported unit: {unit}")
        if lines < 1 or lines > 500:
            raise CommandValidationError("Line count must be in range 1..500")
        return ["journalctl", "--unit", unit, "-n", str(lines), "--no-pager"]

    def bind_reload(self, zone: str | None = None) -> list[str]:
        """Build rndc reload command.

        Args:
            zone: Optional zone name.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If zone is not in allow-list.
        """

        if zone is None:
            return ["rndc", "reload"]
        if zone not in self.allowed_zones:
            raise CommandValidationError(f"Unsupported zone: {zone}")
        return ["rndc", "reload", zone]
