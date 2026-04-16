"""Bootstrap helpers for preparing command pipeline foundation."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.adapter_handlers import (
    AclAdapterCommandHandler,
    AuditAdapterCommandHandler,
    WhoAmIAdapterCommandHandler,
)
from serverbot.application.commanding.handlers import PlaceholderHandler
from serverbot.application.commanding.ops_adapter_handlers import OpsAdapterCommandHandler
from serverbot.application.commanding.scripted_handler import ScriptedCommandHandler
from serverbot.application.commanding.pipeline import CommandPipeline
from serverbot.application.commanding.registry import CommandRegistry
from serverbot.application.commanding.validation import CommandArgumentValidator
from serverbot.application.rpz_service import RpzService
from serverbot.application.services import PolicyService
from serverbot.domain.commanding.models import CommandDescriptor
from serverbot.domain.commanding.script_models import CommandDefinition
from serverbot.domain.models import CommandPolicy
from serverbot.infrastructure.command_catalog import CommandCatalog
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
        allowed_units: tuple[str, ...] = tuple(),
        allowed_zones: tuple[str, ...] = tuple(),
        rpz_service: RpzService | None = None,
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
        command_catalog = CommandCatalog(
            allowed_units=frozenset(allowed_units),
            allowed_zones=frozenset(allowed_zones),
        )
        adapter_handlers = {
            "acl": AclAdapterCommandHandler(acl_service=acl_service),
            "audit": AuditAdapterCommandHandler(audit_service=audit_service),
            "whoami": WhoAmIAdapterCommandHandler(acl_service=acl_service),
            "status": OpsAdapterCommandHandler(
                command_name="status",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "docker": OpsAdapterCommandHandler(
                command_name="docker",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "services": OpsAdapterCommandHandler(
                command_name="services",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "logs": OpsAdapterCommandHandler(
                command_name="logs",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "bind": OpsAdapterCommandHandler(
                command_name="bind",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "exec": OpsAdapterCommandHandler(
                command_name="exec",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
            "rpz": OpsAdapterCommandHandler(
                command_name="rpz",
                command_catalog=command_catalog,
                command_runner=runner,
                rpz_service=rpz_service,
            ),
        }
        for descriptor in self.descriptors:
            adapter_handler = adapter_handlers.get(descriptor.name)
            if adapter_handler is not None:
                registry.register(descriptor=descriptor, handler=adapter_handler)
                continue
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
