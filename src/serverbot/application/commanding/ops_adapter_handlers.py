"""Adapter-backed handlers for operational command groups."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.commanding.contracts import CommandHandler
from serverbot.application.rpz_service import RpzService
from serverbot.domain.commanding.models import CommandRequest, CommandResponse
from serverbot.domain.errors import CommandExecutionError, DomainError
from serverbot.domain.ports import CommandRunner
from serverbot.infrastructure.command_catalog import CommandCatalog, CommandValidationError


@dataclass(frozen=True)
class OpsAdapterCommandHandler(CommandHandler):
    """Execute operational command groups through validated command catalog.

    Args:
        command_name: Root command name.
        command_catalog: Command template registry.
        command_runner: Async subprocess runner.
    """

    command_name: str
    command_catalog: CommandCatalog
    command_runner: CommandRunner
    rpz_service: RpzService | None = None

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Route and execute one operational command.

        Args:
            request: Incoming command request.

        Returns:
            Structured command response.

        Raises:
            DomainError: If command arguments are invalid.
            CommandExecutionError: If command execution fails.
        """

        try:
            if self.command_name == "status":
                return await self._handle_status(request)
            if self.command_name == "docker":
                return await self._handle_docker(request)
            if self.command_name == "services":
                return await self._handle_services(request)
            if self.command_name == "logs":
                return await self._handle_logs(request)
            if self.command_name == "bind":
                return await self._handle_bind(request)
            if self.command_name == "exec":
                return await self._handle_exec(request)
            if self.command_name == "rpz":
                return await self._handle_rpz(request)
        except CommandValidationError as error:
            raise DomainError(str(error), "COMMAND_VALIDATION_FAILED") from error
        raise DomainError(f"Unsupported adapter command: {self.command_name}", "ADAPTER_COMMAND_UNSUPPORTED")

    async def _handle_status(self, request: CommandRequest) -> CommandResponse:
        """Handle status command through system tools.

        Args:
            request: Incoming command request.

        Returns:
            Command response for status operation.
        """

        if request.raw_tokens and request.raw_tokens[0] == "full":
            command = ["bash", "-lc", "uptime && free -h && ip -brief addr"]
            return await self._run_and_respond(request.command_name, command)
        command = ["bash", "-lc", "uptime && free -h"]
        return await self._run_and_respond(request.command_name, command)

    async def _handle_docker(self, request: CommandRequest) -> CommandResponse:
        """Handle docker command group.

        Args:
            request: Incoming command request.

        Returns:
            Command response for docker action.

        Raises:
            DomainError: If subcommand is invalid.
        """

        if not request.raw_tokens:
            raise DomainError("Usage: /docker <subcommand>", "DOCKER_SUBCOMMAND_REQUIRED")
        subcommand = request.raw_tokens[0]
        if subcommand == "ls":
            return await self._run_and_respond(request.command_name, self.command_catalog.docker_ls())
        if subcommand == "ps":
            return await self._run_and_respond(request.command_name, self.command_catalog.docker_ps(include_all=False))
        if subcommand == "ps-all":
            return await self._run_and_respond(request.command_name, self.command_catalog.docker_ps(include_all=True))
        if subcommand in {"inspect", "restart", "stop", "start"}:
            return await self._handle_docker_by_name(request.command_name, subcommand, request.raw_tokens)
        raise DomainError(f"Unsupported docker subcommand: {subcommand}", "DOCKER_SUBCOMMAND_INVALID")

    async def _handle_docker_by_name(
        self,
        command_name: str,
        subcommand: str,
        tokens: tuple[str, ...],
    ) -> CommandResponse:
        """Handle docker subcommands requiring container name.

        Args:
            command_name: Root command name.
            subcommand: Docker subcommand name.
            tokens: Raw command tokens.

        Returns:
            Command response for docker action.

        Raises:
            DomainError: If container name is missing.
        """

        container_name = self._required_token(tokens, 1, "container_name")
        if subcommand == "inspect":
            command = self.command_catalog.docker_inspect(container_name)
        elif subcommand == "restart":
            command = self.command_catalog.docker_restart(container_name)
        elif subcommand == "stop":
            command = self.command_catalog.docker_stop(container_name)
        else:
            command = self.command_catalog.docker_start(container_name)
        return await self._run_and_respond(command_name, command)

    async def _handle_services(self, request: CommandRequest) -> CommandResponse:
        """Handle services command group.

        Args:
            request: Incoming command request.

        Returns:
            Command response for services action.

        Raises:
            DomainError: If subcommand is invalid.
        """

        subcommand = self._required_token(request.raw_tokens, 0, "subcommand")
        unit = self._required_token(request.raw_tokens, 1, "unit")
        if subcommand == "status":
            command = self.command_catalog.systemctl_status(unit)
        elif subcommand == "restart":
            command = self.command_catalog.systemctl_restart(unit)
        elif subcommand == "reload":
            command = self.command_catalog.systemctl_reload(unit)
        else:
            raise DomainError(f"Unsupported services subcommand: {subcommand}", "SERVICES_SUBCOMMAND_INVALID")
        return await self._run_and_respond(request.command_name, command)

    async def _handle_logs(self, request: CommandRequest) -> CommandResponse:
        """Handle logs command group.

        Args:
            request: Incoming command request.

        Returns:
            Command response for logs action.

        Raises:
            DomainError: If subcommand is invalid.
        """

        subcommand = self._required_token(request.raw_tokens, 0, "subcommand")
        if subcommand == "unit":
            unit = self._required_token(request.raw_tokens, 1, "unit")
            lines = self._optional_int(request.raw_tokens, 2, default_value=100)
            return await self._run_and_respond(request.command_name, self.command_catalog.journal_unit(unit, lines))
        if subcommand == "docker":
            container = self._required_token(request.raw_tokens, 1, "container_name")
            lines = self._optional_int(request.raw_tokens, 2, default_value=100)
            return await self._run_and_respond(request.command_name, self.command_catalog.docker_logs(container, lines))
        return CommandResponse(
            command_name=request.command_name,
            message="Usage: /logs unit <service> [N] | /logs docker <container> [N]",
            success=True,
        )

    async def _handle_bind(self, request: CommandRequest) -> CommandResponse:
        """Handle bind command group.

        Args:
            request: Incoming command request.

        Returns:
            Command response for bind action.

        Raises:
            DomainError: If subcommand is invalid.
        """

        subcommand = self._required_token(request.raw_tokens, 0, "subcommand")
        if subcommand == "checkconf":
            return await self._run_and_respond(request.command_name, self.command_catalog.named_checkconf())
        if subcommand == "checkzone":
            zone = self._required_token(request.raw_tokens, 1, "zone")
            zone_file = self._required_token(request.raw_tokens, 2, "zone_file")
            return await self._run_and_respond(request.command_name, self.command_catalog.named_checkzone(zone, zone_file))
        if subcommand == "reconfig":
            return await self._run_and_respond(request.command_name, self.command_catalog.bind_reconfig())
        if subcommand == "reload":
            return await self._run_and_respond(request.command_name, self.command_catalog.bind_reload())
        if subcommand == "reload-zone":
            zone = self._required_token(request.raw_tokens, 1, "zone")
            return await self._run_and_respond(request.command_name, self.command_catalog.bind_reload(zone))
        if subcommand == "flush":
            return await self._run_and_respond(request.command_name, self.command_catalog.bind_flush())
        raise DomainError(f"Unsupported bind subcommand: {subcommand}", "BIND_SUBCOMMAND_INVALID")

    async def _handle_exec(self, request: CommandRequest) -> CommandResponse:
        """Handle exec template command group.

        Args:
            request: Incoming command request.

        Returns:
            Command response for exec action.

        Raises:
            DomainError: If template key is unsupported.
        """

        template = self._required_token(request.raw_tokens, 0, "template")
        if template == "bind_reload":
            return await self._run_and_respond(request.command_name, self.command_catalog.bind_reload())
        if template == "journal_unit":
            unit = self._required_token(request.raw_tokens, 1, "unit")
            lines = self._optional_int(request.raw_tokens, 2, default_value=100)
            return await self._run_and_respond(request.command_name, self.command_catalog.journal_unit(unit, lines))
        if template == "named_checkzone":
            zone = self._required_token(request.raw_tokens, 1, "zone")
            zone_file = self._required_token(request.raw_tokens, 2, "zone_file")
            return await self._run_and_respond(request.command_name, self.command_catalog.named_checkzone(zone, zone_file))
        raise DomainError(f"Unsupported exec template: {template}", "EXEC_TEMPLATE_INVALID")

    async def _handle_rpz(self, request: CommandRequest) -> CommandResponse:
        """Handle RPZ command group through BIND-backed adapters.

        Args:
            request: Incoming command request.

        Returns:
            Command response for RPZ action.
        """

        if self.rpz_service is None:
            raise DomainError("RPZ service is not configured.", "RPZ_SERVICE_NOT_CONFIGURED")
        subcommand = self._required_token(request.raw_tokens, 0, "subcommand")
        if subcommand == "list":
            rules = self.rpz_service.list_rules()
            if not rules:
                return CommandResponse(command_name=request.command_name, message="RPZ list is empty.", success=True)
            lines = [f"{item.qname} -> {item.policy} {item.value}".strip() for item in rules]
            return CommandResponse(command_name=request.command_name, message="\n".join(lines), success=True)
        if subcommand == "find":
            query = self._required_token(request.raw_tokens, 1, "query")
            rules = self.rpz_service.find_rules(query)
            if not rules:
                return CommandResponse(command_name=request.command_name, message="No matching RPZ rules.", success=True)
            lines = [f"{item.qname} -> {item.policy} {item.value}".strip() for item in rules]
            return CommandResponse(command_name=request.command_name, message="\n".join(lines), success=True)
        if subcommand == "add":
            qname = self._required_token(request.raw_tokens, 1, "qname")
            policy = self._required_token(request.raw_tokens, 2, "policy")
            value = request.raw_tokens[3].strip() if len(request.raw_tokens) > 3 else ""
            record = await self.rpz_service.add_rule(qname=qname, policy=policy, value=value)
            return CommandResponse(
                command_name=request.command_name,
                message=f"RPZ rule saved: {record.qname} -> {record.policy} {record.value}".strip(),
                success=True,
            )
        if subcommand == "del":
            qname = self._required_token(request.raw_tokens, 1, "qname")
            deleted = await self.rpz_service.delete_rule(qname=qname)
            if not deleted:
                return CommandResponse(command_name=request.command_name, message="RPZ rule not found.", success=True)
            return CommandResponse(command_name=request.command_name, message=f"RPZ rule deleted: {qname}", success=True)
        raise DomainError(f"Unsupported rpz subcommand: {subcommand}", "RPZ_SUBCOMMAND_INVALID")

    async def _run_and_respond(self, command_name: str, command: list[str]) -> CommandResponse:
        """Execute external command and map result to response model.

        Args:
            command_name: Root command name.
            command: Validated command vector.

        Returns:
            Structured command response.

        Raises:
            CommandExecutionError: If command execution fails.
            DomainError: If command validation fails.
        """

        result = await self.command_runner.run(command)
        if result.return_code != 0:
            message = result.stderr.strip() or result.stdout.strip() or "Command failed."
            raise CommandExecutionError(message, "COMMAND_EXECUTION_FAILED")
        output = result.stdout.strip() or "OK"
        return CommandResponse(command_name=command_name, message=output, success=True)

    def _required_token(self, tokens: tuple[str, ...], index: int, token_name: str) -> str:
        """Read required token from command tuple.

        Args:
            tokens: Source token tuple.
            index: Zero-based token index.
            token_name: Human-readable token name.

        Returns:
            Parsed token string.

        Raises:
            DomainError: If token is missing or empty.
        """

        if len(tokens) <= index or not tokens[index].strip():
            raise DomainError(f"Missing required argument: {token_name}", "COMMAND_ARGUMENT_REQUIRED")
        return tokens[index].strip()

    def _optional_int(self, tokens: tuple[str, ...], index: int, default_value: int) -> int:
        """Parse optional integer token.

        Args:
            tokens: Source token tuple.
            index: Zero-based token index.
            default_value: Value used when token is missing.

        Returns:
            Parsed integer value.

        Raises:
            DomainError: If token is not a valid integer.
        """

        if len(tokens) <= index:
            return default_value
        raw_value = tokens[index].strip()
        if not raw_value.isdigit():
            raise DomainError("Numeric argument must be integer.", "COMMAND_ARGUMENT_NOT_INTEGER")
        return int(raw_value)
