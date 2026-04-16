"""Use-case orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.services import AuditService, PolicyService
from serverbot.domain.models import Principal


@dataclass(frozen=True)
class ExecuteCommandUseCase:
    """Execute command while enforcing ACL and audit.

    Args:
        policy_service: ACL decision service.
        audit_service: Audit service.
    """

    policy_service: PolicyService
    audit_service: AuditService

    async def execute(self, principal: Principal, command_name: str) -> bool:
        """Run ACL validation and emit audit event.

        Args:
            principal: Actor requesting action.
            command_name: Action identifier.

        Returns:
            True when command is allowed.
        """

        allowed = self.policy_service.is_allowed(principal, command_name)
        self.audit_service.record(principal, command_name, allowed)
        return allowed
