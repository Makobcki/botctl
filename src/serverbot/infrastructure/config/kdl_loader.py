"""KDL configuration loader implementation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from serverbot.domain.errors import DomainError
from serverbot.domain.ports import AppConfig, ConfigLoader


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

        raw_values = self._parse_pairs(file_path.read_text(encoding="utf-8"))
        required_keys = {
            "telegram_token",
            "alert_chat_id",
            "verbose",
            "worker_interval_seconds",
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
            allowed_units=tuple(self._parse_list(raw_values["allowed_units"])),
            allowed_zones=tuple(self._parse_list(raw_values["allowed_zones"])),
        )

    def _parse_pairs(self, content: str) -> dict[str, str]:
        """Parse `key value` KDL-style lines.

        Args:
            content: Raw file content.

        Returns:
            Mapping of key-value tokens.

        Raises:
            DomainError: If line structure is invalid.
        """

        mapping: dict[str, str] = {}
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            match = re.fullmatch(r"([a-z_]+)\s+(.+)", stripped)
            if match is None:
                raise DomainError(f"Invalid KDL line: {line}", "CONFIG_PARSE_ERROR")
            key = match.group(1)
            value = match.group(2).strip().strip('"')
            mapping[key] = value
        return mapping

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
