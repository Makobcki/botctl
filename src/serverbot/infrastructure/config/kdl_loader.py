"""KDL configuration loader implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.alerts import AlertCheckDescriptor
from serverbot.domain.commanding.models import CommandArgumentDescriptor, CommandDescriptor
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

        raw_values, command_descriptors, alert_checks, bootstrap_grants = self._parse_document(
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
        if not command_descriptors:
            raise DomainError("At least one command must be configured.", "CONFIG_MISSING_COMMANDS")

        return AppConfig(
            telegram_token=raw_values["telegram_token"],
            alert_chat_id=int(raw_values["alert_chat_id"]),
            verbose=raw_values["verbose"].lower() == "true",
            worker_interval_seconds=int(raw_values["worker_interval_seconds"]),
            db_path=raw_values["db_path"],
            allowed_units=tuple(self._parse_list(raw_values["allowed_units"])),
            allowed_zones=tuple(self._parse_list(raw_values["allowed_zones"])),
            command_descriptors=tuple(command_descriptors),
            alert_checks=tuple(alert_checks),
            bootstrap_grants=tuple(bootstrap_grants),
        )

    def _parse_document(
        self,
        content: str,
    ) -> tuple[
        dict[str, str],
        list[CommandDescriptor],
        list[AlertCheckDescriptor],
        list[PrincipalGrantDescriptor],
    ]:
        """Parse KDL document into scalar settings and command descriptors.

        Args:
            content: Raw file content.

        Returns:
            Parsed scalar settings and command descriptor list.

        Raises:
            DomainError: If line structure is invalid.
        """

        mapping: dict[str, str] = {}
        command_definitions: dict[str, CommandDescriptor] = {}
        argument_map: dict[str, list[CommandArgumentDescriptor]] = {}
        alert_checks: list[AlertCheckDescriptor] = []
        bootstrap_grants: list[PrincipalGrantDescriptor] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            if stripped.startswith("command "):
                descriptor = self._parse_command_descriptor(stripped)
                command_definitions[descriptor.name] = descriptor
                continue
            if stripped.startswith("command_arg "):
                command_name, argument_descriptor = self._parse_command_argument_descriptor(stripped)
                if command_name not in command_definitions:
                    raise DomainError(
                        f"command_arg references unknown command: {command_name}",
                        "CONFIG_COMMAND_ARG_UNKNOWN_COMMAND",
                    )
                argument_map.setdefault(command_name, []).append(argument_descriptor)
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
        command_descriptors = self._build_command_descriptors(command_definitions, argument_map)
        return mapping, command_descriptors, alert_checks, bootstrap_grants

    def _parse_command_descriptor(self, line: str) -> CommandDescriptor:
        """Parse one `command` declaration line.

        Args:
            line: Raw KDL line starting with `command`.

        Returns:
            Parsed command descriptor.

        Raises:
            DomainError: If command declaration format is invalid.
        """

        pattern = (
            r'command\s+"(?P<name>[a-z0-9._-]+)"\s+'
            r'tag="(?P<tag>[a-z0-9._-]+)"\s+'
            r'description="(?P<description>[^"]+)"'
        )
        match = re.fullmatch(pattern, line)
        if match is None:
            raise DomainError(f"Invalid command declaration: {line}", "CONFIG_COMMAND_PARSE_ERROR")
        return CommandDescriptor(
            name=match.group("name"),
            required_tag=match.group("tag"),
            description=match.group("description"),
        )

    def _parse_command_argument_descriptor(
        self,
        line: str,
    ) -> tuple[str, CommandArgumentDescriptor]:
        """Parse one `command_arg` declaration line.

        Args:
            line: Raw KDL line starting with `command_arg`.

        Returns:
            Pair of command name and parsed argument descriptor.

        Raises:
            DomainError: If argument declaration format is invalid.
        """

        pattern = (
            r'command_arg\s+"(?P<command_name>[a-z0-9._-]+)"\s+'
            r'name="(?P<name>[a-z0-9._-]+)"\s+'
            r'type="(?P<value_type>str|int)"\s+'
            r'required=(?P<required>true|false)'
        )
        match = re.fullmatch(pattern, line)
        if match is None:
            raise DomainError(f"Invalid command_arg declaration: {line}", "CONFIG_COMMAND_ARG_PARSE_ERROR")
        return (
            match.group("command_name"),
            CommandArgumentDescriptor(
                name=match.group("name"),
                value_type=match.group("value_type"),
                required=match.group("required") == "true",
            ),
        )

    def _build_command_descriptors(
        self,
        command_definitions: dict[str, CommandDescriptor],
        argument_map: dict[str, list[CommandArgumentDescriptor]],
    ) -> list[CommandDescriptor]:
        """Attach parsed argument definitions to command descriptors.

        Args:
            command_definitions: Base descriptors by command name.
            argument_map: Parsed command arguments grouped by command name.

        Returns:
            Sorted command descriptor list with argument metadata.

        Raises:
            None.
        """

        result: list[CommandDescriptor] = []
        for command_name, descriptor in sorted(command_definitions.items()):
            arguments = tuple(argument_map.get(command_name, []))
            result.append(
                CommandDescriptor(
                    name=descriptor.name,
                    required_tag=descriptor.required_tag,
                    description=descriptor.description,
                    arguments=arguments,
                )
            )
        return result

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
