"""Bootstrap helpers for preparing command pipeline foundation."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.scripted_handler import ScriptedCommandHandler
from serverbot.application.commanding.pipeline import CommandPipeline
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.validation import CommandArgumentValidator
from serverbot.application.services import PolicyService
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.domain.commanding.script_models import CommandDefinition
from serverbot.domain.models import CommandPolicy
from serverbot.infrastructure.system.subprocess_runner import AsyncSubprocessRunner


@dataclass(frozen=True)
class CommandCatalogBootstrap:
    """Bootstrapper for command descriptors and placeholder handlers.

    Args:
        descriptors: Command descriptors to register.
    """

    descriptors: tuple[CommandDescriptor, ...]
    definitions: tuple[CommandDefinition, ...] = tuple()

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
        definition_map = {definition.descriptor.name: definition for definition in self.definitions}
        runner = AsyncSubprocessRunner()
        for descriptor in self.descriptors:
            definition = definition_map.get(descriptor.name)
            if definition is not None:
                registry.register(
                    descriptor=descriptor,
                    handler=ScriptedCommandHandler(
                        command_name=descriptor.name,
                        runner=runner,
                        root_execute=definition.root_execute,
                        root_except_rules=definition.root_except_rules,
                        subcommands=definition.subcommands,
                    ),
                )
                continue
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
