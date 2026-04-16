"""Bootstrap helpers for preparing command pipeline foundation."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.pipeline import CommandPipeline
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.validation import CommandArgumentValidator
from serverbot.application.services import PolicyService
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.domain.models import CommandPolicy


@dataclass(frozen=True)
class CommandCatalogBootstrap:
    """Bootstrapper for command descriptors and placeholder handlers.

    Args:
        descriptors: Command descriptors to register.
    """

    descriptors: tuple[CommandDescriptor, ...]

    def build_pipeline(
        self,
        acl_service: AclService,
        audit_service: PersistentAuditService,
    ) -> CommandPipeline:
        """Create configured command pipeline with placeholder handlers.

        Args:
            acl_service: Principal/tag service.
            audit_service: Persistent audit service.

        Returns:
            Ready-to-use command pipeline.

        Raises:
            Exception: Propagates registration and setup failures.
        """

        policies = {
            descriptor.name: CommandPolicy(
                command_name=descriptor.name,
                required_tag=descriptor.required_tag,
            )
            for descriptor in self.descriptors
        }
        policy_service = PolicyService(policies=policies)
        registry = CommandRegistry()
        for descriptor in self.descriptors:
            registry.register(
                descriptor=descriptor,
                handler=PlaceholderHandler(
                    response_message=f"Command '{descriptor.name}' is prepared but not implemented yet.",
                ),
            )
        return CommandPipeline(
            acl_service=acl_service,
            policy_service=policy_service,
            audit_service=audit_service,
            command_registry=registry,
            argument_validator=CommandArgumentValidator(),
        )
