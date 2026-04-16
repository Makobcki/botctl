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

    def systemctl_status(self, unit: str) -> list[str]:
        """Build systemctl status command.

        Args:
            unit: Allowed unit name.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If unit is not in allow-list.
        """

        self._validate_unit(unit)
        return ["systemctl", "status", unit, "--no-pager"]

    def systemctl_restart(self, unit: str) -> list[str]:
        """Build systemctl restart command.

        Args:
            unit: Allowed unit name.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If unit is not in allow-list.
        """

        self._validate_unit(unit)
        return ["systemctl", "restart", unit]

    def systemctl_reload(self, unit: str) -> list[str]:
        """Build systemctl reload command.

        Args:
            unit: Allowed unit name.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If unit is not in allow-list.
        """

        self._validate_unit(unit)
        return ["systemctl", "reload", unit]

    def docker_ls(self) -> list[str]:
        """Build docker list running containers command.

        Args:
            None.

        Returns:
            Argument vector for subprocess.
        """

        return ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"]

    def docker_ps(self, include_all: bool) -> list[str]:
        """Build docker ps command.

        Args:
            include_all: Whether stopped containers should be included.

        Returns:
            Argument vector for subprocess.
        """

        return ["docker", "ps", "-a"] if include_all else ["docker", "ps"]

    def docker_inspect(self, container_name: str) -> list[str]:
        """Build docker inspect command.

        Args:
            container_name: Container name or id.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If container name is invalid.
        """

        self._validate_non_empty_token(container_name, "container_name")
        return ["docker", "inspect", container_name]

    def docker_restart(self, container_name: str) -> list[str]:
        """Build docker restart command.

        Args:
            container_name: Container name or id.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If container name is invalid.
        """

        self._validate_non_empty_token(container_name, "container_name")
        return ["docker", "restart", container_name]

    def docker_stop(self, container_name: str) -> list[str]:
        """Build docker stop command.

        Args:
            container_name: Container name or id.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If container name is invalid.
        """

        self._validate_non_empty_token(container_name, "container_name")
        return ["docker", "stop", container_name]

    def docker_start(self, container_name: str) -> list[str]:
        """Build docker start command.

        Args:
            container_name: Container name or id.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If container name is invalid.
        """

        self._validate_non_empty_token(container_name, "container_name")
        return ["docker", "start", container_name]

    def docker_logs(self, container_name: str, lines: int) -> list[str]:
        """Build docker logs command.

        Args:
            container_name: Container name or id.
            lines: Maximum output lines.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If arguments are invalid.
        """

        self._validate_non_empty_token(container_name, "container_name")
        if lines < 1 or lines > 500:
            raise CommandValidationError("Line count must be in range 1..500")
        return ["docker", "logs", "--tail", str(lines), container_name]

    def named_checkconf(self) -> list[str]:
        """Build named-checkconf command.

        Args:
            None.

        Returns:
            Argument vector for subprocess.
        """

        return ["named-checkconf"]

    def named_checkzone(self, zone: str, zone_file: str) -> list[str]:
        """Build named-checkzone command.

        Args:
            zone: DNS zone name.
            zone_file: Zone file path.

        Returns:
            Argument vector for subprocess.

        Raises:
            CommandValidationError: If arguments are invalid.
        """

        if zone not in self.allowed_zones:
            raise CommandValidationError(f"Unsupported zone: {zone}")
        self._validate_non_empty_token(zone_file, "zone_file")
        return ["named-checkzone", zone, zone_file]

    def bind_reconfig(self) -> list[str]:
        """Build rndc reconfig command.

        Args:
            None.

        Returns:
            Argument vector for subprocess.
        """

        return ["rndc", "reconfig"]

    def bind_flush(self) -> list[str]:
        """Build rndc flush command.

        Args:
            None.

        Returns:
            Argument vector for subprocess.
        """

        return ["rndc", "flush"]

    def _validate_unit(self, unit: str) -> None:
        """Validate systemd unit name against allow-list.

        Args:
            unit: Unit name to validate.

        Returns:
            None.

        Raises:
            CommandValidationError: If unit is not allowed.
        """

        if unit not in self.allowed_units:
            raise CommandValidationError(f"Unsupported unit: {unit}")

    def _validate_non_empty_token(self, value: str, field_name: str) -> None:
        """Validate plain non-empty token argument.

        Args:
            value: Input token.
            field_name: Argument field name.

        Returns:
            None.

        Raises:
            CommandValidationError: If value is empty.
        """

        if not value.strip():
            raise CommandValidationError(f"{field_name} must be non-empty")
