"""Use-case orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.services import AuditService, PolicyService
from serverbot.domain.errors import AuthorizationError
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


@dataclass(frozen=True)
class ExecuteAuthorizedCommandUseCase:
    """Execute command using ACL repository data and persistent auditing.

    Args:
        acl_service: Service resolving principals and tags.
        policy_service: ACL policy evaluator.
        audit_service: Persistent audit writer.
    """

    acl_service: AclService
    policy_service: PolicyService
    audit_service: PersistentAuditService

    async def execute(self, principal_id: int, command_name: str) -> None:
        """Authorize command and persist execution audit.

        Args:
            principal_id: Telegram principal identifier.
            command_name: Requested command name.

        Returns:
            None.

        Raises:
            AuthorizationError: If principal lacks required permissions.
        """

        principal = self.acl_service.get_principal(principal_id)
        allowed = self.policy_service.is_allowed(principal, command_name)
        self.audit_service.record(principal_id=principal_id, command_name=command_name, success=allowed)
        if not allowed:
            raise AuthorizationError("Command access denied.", "ACL_DENIED")
