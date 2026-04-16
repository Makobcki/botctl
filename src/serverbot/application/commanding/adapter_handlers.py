"""Adapter-backed command handlers for ACL and audit workflows."""

from __future__ import annotations

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.audit_service import PersistentAuditService
from serverbot.application.commanding.contracts import CommandHandler
from serverbot.domain.commanding.models import CommandRequest, CommandResponse
from serverbot.domain.errors import DomainError


@dataclass(frozen=True)
class AclAdapterCommandHandler(CommandHandler):
    """Handle ACL commands using repository-backed ACL service.

    Args:
        acl_service: Service for principal tag management.
    """

    acl_service: AclService

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Execute ACL management subcommands.

        Args:
            request: Incoming command request.

        Returns:
            Structured command response.

        Raises:
            DomainError: If subcommand or arguments are invalid.
        """

        if not request.raw_tokens:
            raise DomainError("ACL subcommand is required.", "ACL_SUBCOMMAND_REQUIRED")
        subcommand = request.raw_tokens[0]
        if subcommand == "list":
            return self._handle_list(request.principal_id, request.command_name)
        if subcommand in {"add-user", "add-chat", "grant"}:
            return self._handle_grant(request.command_name, request.raw_tokens)
        if subcommand == "revoke":
            return self._handle_revoke(request.command_name, request.raw_tokens)
        raise DomainError(f"Unsupported ACL subcommand: {subcommand}", "ACL_SUBCOMMAND_UNSUPPORTED")

    def _handle_list(self, principal_id: int, command_name: str) -> CommandResponse:
        """Render tags for caller principal.

        Args:
            principal_id: Caller telegram identifier.
            command_name: Base command name.

        Returns:
            Command response with sorted tags.
        """

        principal = self.acl_service.get_principal(principal_id)
        tags = ", ".join(sorted(principal.tags)) if principal.tags else "<none>"
        return CommandResponse(
            command_name=command_name,
            message=f"Principal {principal.telegram_id} tags: {tags}",
            success=True,
        )

    def _handle_grant(self, command_name: str, tokens: tuple[str, ...]) -> CommandResponse:
        """Grant one tag to a principal.

        Args:
            command_name: Base command name.
            tokens: Raw tokens including subcommand and arguments.

        Returns:
            Success response.

        Raises:
            DomainError: If principal or tag are missing/invalid.
        """

        principal_id, tag = self._parse_principal_and_tag(tokens)
        self.acl_service.grant_tag(principal_id, tag)
        return CommandResponse(
            command_name=command_name,
            message=f"Granted tag '{tag}' to principal {principal_id}.",
            success=True,
        )

    def _handle_revoke(self, command_name: str, tokens: tuple[str, ...]) -> CommandResponse:
        """Revoke one tag from a principal.

        Args:
            command_name: Base command name.
            tokens: Raw tokens including subcommand and arguments.

        Returns:
            Success response.

        Raises:
            DomainError: If principal or tag are missing/invalid.
        """

        principal_id, tag = self._parse_principal_and_tag(tokens)
        self.acl_service.revoke_tag(principal_id, tag)
        return CommandResponse(
            command_name=command_name,
            message=f"Revoked tag '{tag}' from principal {principal_id}.",
            success=True,
        )

    def _parse_principal_and_tag(self, tokens: tuple[str, ...]) -> tuple[int, str]:
        """Parse principal identifier and tag from raw tokens.

        Args:
            tokens: Raw command tokens.

        Returns:
            Parsed principal identifier and tag.

        Raises:
            DomainError: If arguments are missing or malformed.
        """

        if len(tokens) < 3:
            raise DomainError("Usage: /acl <subcommand> <principal_id> <tag>", "ACL_ARGUMENTS_INVALID")
        principal_raw = tokens[1]
        if not principal_raw.isdigit():
            raise DomainError("principal_id must be an integer.", "ACL_PRINCIPAL_ID_INVALID")
        tag = tokens[2].strip()
        if not tag:
            raise DomainError("Tag must be non-empty.", "ACL_TAG_INVALID")
        return int(principal_raw), tag


@dataclass(frozen=True)
class AuditAdapterCommandHandler(CommandHandler):
    """Handle audit commands using persistent audit repository.

    Args:
        audit_service: Persistent audit service.
    """

    audit_service: PersistentAuditService

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Execute audit subcommands.

        Args:
            request: Incoming command request.

        Returns:
            Structured command response.

        Raises:
            DomainError: If subcommand or limit are invalid.
        """

        if not request.raw_tokens or request.raw_tokens[0] != "last":
            raise DomainError("Usage: /audit last [limit]", "AUDIT_SUBCOMMAND_INVALID")
        limit = 20
        if len(request.raw_tokens) > 1:
            limit_raw = request.raw_tokens[1]
            if not limit_raw.isdigit():
                raise DomainError("Audit limit must be an integer.", "AUDIT_LIMIT_INVALID")
            limit = max(1, min(200, int(limit_raw)))
        rows = self.audit_service.list_recent(limit)
        if not rows:
            message = "No audit events yet."
        else:
            lines = [
                f"{index + 1}. principal={row.principal_id} command={row.command_name} success={row.success}"
                for index, row in enumerate(rows)
            ]
            message = "\n".join(lines)
        return CommandResponse(command_name=request.command_name, message=message, success=True)


@dataclass(frozen=True)
class WhoAmIAdapterCommandHandler(CommandHandler):
    """Resolve caller principal from ACL repository.

    Args:
        acl_service: Service for principal/tag lookup.
    """

    acl_service: AclService

    async def handle(self, request: CommandRequest) -> CommandResponse:
        """Render principal identity and tag grants.

        Args:
            request: Incoming command request.

        Returns:
            Structured command response.

        Raises:
            None.
        """

        principal = self.acl_service.get_principal(request.principal_id)
        tags = ", ".join(sorted(principal.tags)) if principal.tags else "<none>"
        return CommandResponse(
            command_name=request.command_name,
            message=f"Principal: {principal.telegram_id}\nTags: {tags}",
            success=True,
        )
