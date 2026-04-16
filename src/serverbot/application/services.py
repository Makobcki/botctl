"""Application service layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.domain.models import CommandPolicy, Principal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyService:
    """Service that decides whether a principal can execute a command.

    Args:
        policies: Map of command names to required tag names.
    """

    policies: dict[str, CommandPolicy]

    def is_allowed(self, principal: Principal, command_name: str) -> bool:
        """Check whether principal may execute command.

        Args:
            principal: Actor requesting command execution.
            command_name: Incoming command name.

        Returns:
            True when ACL allows the command, False otherwise.
        """

        policy = self.policies.get(command_name)
        if policy is None:
            logger.debug("No policy for command '%s'; deny by default.", command_name)
            return False
        allowed = policy.required_tag in principal.tags
        logger.debug(
            "ACL decision command='%s' principal=%s allowed=%s",
            command_name,
            principal.telegram_id,
            allowed,
        )
        return allowed


@dataclass(frozen=True)
class AuditService:
    """Service producing structured audit lines.

    Args:
        logger_name: Logger name for audit events.
    """

    logger_name: str = "serverbot.audit"

    def record(self, principal: Principal, command_name: str, success: bool) -> None:
        """Record command execution result.

        Args:
            principal: Actor who invoked command.
            command_name: Command name.
            success: Whether command succeeded.

        Returns:
            None
        """

        audit_logger = logging.getLogger(self.logger_name)
        audit_logger.info(
            "audit principal=%s command=%s success=%s",
            principal.telegram_id,
            command_name,
            success,
        )
