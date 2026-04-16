"""KDL configuration loader implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.alerts import AlertCheckDescriptor
from serverbot.domain.errors import DomainError
from serverbot.domain.ports import AppConfig, ConfigLoader
from serverbot.domain.security import PrincipalGrantDescriptor


@dataclass(frozen=True)
class KdlConfigLoader(ConfigLoader):
    """Load strongly-typed settings from a constrained KDL file.

    Args:
        None.

    Returns:
        None.
    """

    def load(self, path: str) -> AppConfig:
        """Parse KDL document and build application config.

        Args:
            path: KDL file path.

        Returns:
            Parsed immutable application config.

        Raises:
            DomainError: If file extension is not `.kdl`.
            DomainError: If required keys are missing.
        """

        file_path = Path(path)
        if file_path.suffix != ".kdl":
            raise DomainError("Configuration file must use .kdl extension.", "CONFIG_EXT_INVALID")

        raw_values, alert_checks, bootstrap_grants = self._parse_document(
            file_path.read_text(encoding="utf-8")
        )
        required_keys = {
            "telegram_token",
            "alert_chat_id",
            "verbose",
            "worker_interval_seconds",
            "db_path",
            "allowed_units",
            "allowed_zones",
        }
        missing = required_keys - raw_values.keys()
        if missing:
            missing_values = ", ".join(sorted(missing))
            raise DomainError(f"Missing keys: {missing_values}", "CONFIG_MISSING_KEY")
        return AppConfig(
            telegram_token=raw_values["telegram_token"],
            alert_chat_id=int(raw_values["alert_chat_id"]),
            verbose=raw_values["verbose"].lower() == "true",
            worker_interval_seconds=int(raw_values["worker_interval_seconds"]),
            db_path=raw_values["db_path"],
            allowed_units=tuple(self._parse_list(raw_values["allowed_units"])),
            allowed_zones=tuple(self._parse_list(raw_values["allowed_zones"])),
            command_descriptors=tuple(),
            alert_checks=tuple(alert_checks),
            bootstrap_grants=tuple(bootstrap_grants),
        )

    def _parse_document(
        self,
        content: str,
    ) -> tuple[dict[str, str], list[AlertCheckDescriptor], list[PrincipalGrantDescriptor]]:
        """Parse KDL document into scalar settings and command descriptors.

        Args:
            content: Raw file content.

        Returns:
            Parsed scalar settings and command descriptor list.

        Raises:
            DomainError: If line structure is invalid.
        """

        mapping: dict[str, str] = {}
        alert_checks: list[AlertCheckDescriptor] = []
        bootstrap_grants: list[PrincipalGrantDescriptor] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            if stripped.startswith("command "):
                raise DomainError(
                    "Command declarations must be stored in commands/*.kdl files.",
                    "CONFIG_COMMAND_DECLARATION_FORBIDDEN",
                )
                continue
            if stripped.startswith("command_arg "):
                raise DomainError(
                    "Command declarations must be stored in commands/*.kdl files.",
                    "CONFIG_COMMAND_DECLARATION_FORBIDDEN",
                )
                continue
            if stripped.startswith("alert_check "):
                alert_checks.append(self._parse_alert_check_descriptor(stripped))
                continue
            if stripped.startswith("principal_grant "):
                bootstrap_grants.append(self._parse_principal_grant(stripped))
                continue
            match = re.fullmatch(r"([a-z_]+)\s+(.+)", stripped)
            if match is None:
                raise DomainError(f"Invalid KDL line: {line}", "CONFIG_PARSE_ERROR")
            key = match.group(1)
            value = match.group(2).strip().strip('"')
            mapping[key] = value
        return mapping, alert_checks, bootstrap_grants

    def _parse_alert_check_descriptor(self, line: str) -> AlertCheckDescriptor:
        """Parse one `alert_check` declaration line.

        Args:
            line: Raw KDL line starting with `alert_check`.

        Returns:
            Parsed checker descriptor.

        Raises:
            DomainError: If declaration format is invalid.
        """

        pattern = (
            r'alert_check\s+"(?P<name>[a-z0-9._-]+)"\s+'
            r'type="(?P<check_type>[a-z0-9._-]+)"\s+'
            r'interval=(?P<interval>[0-9]+)\s+'
            r'enabled=(?P<enabled>true|false)'
        )
        match = re.fullmatch(pattern, line)
        if match is None:
            raise DomainError(f"Invalid alert_check declaration: {line}", "CONFIG_ALERT_CHECK_PARSE_ERROR")
        return AlertCheckDescriptor(
            name=match.group("name"),
            check_type=match.group("check_type"),
            interval_seconds=int(match.group("interval")),
            enabled=match.group("enabled") == "true",
        )

    def _parse_principal_grant(self, line: str) -> PrincipalGrantDescriptor:
        """Parse one `principal_grant` declaration line.

        Args:
            line: Raw KDL line starting with `principal_grant`.

        Returns:
            Parsed principal grant descriptor.

        Raises:
            DomainError: If declaration format is invalid.
        """

        pattern = (
            r'principal_grant\s+"(?P<kind>user|chat):(?P<principal_id>[0-9]+)"\s+'
            r'tag="(?P<tag>[a-z0-9._-]+)"'
        )
        match = re.fullmatch(pattern, line)
        if match is None:
            raise DomainError(f"Invalid principal_grant declaration: {line}", "CONFIG_PRINCIPAL_GRANT_PARSE_ERROR")
        return PrincipalGrantDescriptor(
            principal_kind=match.group("kind"),
            principal_id=int(match.group("principal_id")),
            tag=match.group("tag"),
        )

    def _parse_list(self, value: str) -> list[str]:
        """Parse comma-separated list literals.

        Args:
            value: Serialized list value.

        Returns:
            Parsed list of tokens.

        Raises:
            None.
        """

        cleaned = value.strip().strip("[]")
        if not cleaned:
            return []
        return [item.strip().strip('"') for item in cleaned.split(",") if item.strip()]
