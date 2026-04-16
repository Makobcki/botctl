"""Command dispatch pipeline with ACL and auditing."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.validation import CommandArgumentValidator
from serverbot.application.services import PolicyService
from serverbot.domain.commanding.models import CommandRequest, CommandResponse
from serverbot.domain.errors import DomainError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandPipeline:
    """Dispatch commands through ACL, policy and handler execution.

    Args:
        acl_service: Principal/tag resolution service.
        policy_service: Policy decision service.
        audit_service: Persistent audit service.
        command_registry: Registered commands collection.
        argument_validator: Argument validator service.
    """

    acl_service: AclService
    policy_service: PolicyService
    audit_service: PersistentAuditService
    command_registry: CommandRegistry
    argument_validator: CommandArgumentValidator

    async def dispatch(self, request: CommandRequest) -> CommandResponse:
        """Execute command request through the pipeline.

        Args:
            request: Incoming command request.

        Returns:
            Structured command response from handler.

        Raises:
            Exception: Propagates domain and handler-level errors.
        """

        registered_command = self.command_registry.get(request.command_name)
        principal = self.acl_service.get_principal(request.principal_id)
        if registered_command.descriptor.name not in self.policy_service.policies:
            raise DomainError(
                f"Missing policy for command: {registered_command.descriptor.name}",
                "POLICY_NOT_FOUND",
            )
        allowed = self.policy_service.is_allowed(principal, registered_command.descriptor.name)
        self.audit_service.record(request.principal_id, request.command_name, allowed)
        if not allowed:
            logger.warning(
                "Command denied by ACL principal=%s command=%s",
                request.principal_id,
                request.command_name,
            )
            return CommandResponse(
                command_name=request.command_name,
                message="Access denied.",
                success=False,
            )
        self.argument_validator.validate(
            descriptor=registered_command.descriptor,
            arguments=request.arguments,
        )
        logger.debug(
            "Command allowed principal=%s command=%s",
            request.principal_id,
            request.command_name,
        )
        return await registered_command.handler.handle(request)
