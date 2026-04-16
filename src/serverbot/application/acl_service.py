"""ACL management application service."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.domain.models import Principal
from serverbot.domain.repositories import PrincipalTagRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AclService:
    """Service for principal tag assignments.

    Args:
        principal_tag_repository: Tag repository dependency.
    """

    principal_tag_repository: PrincipalTagRepository

    def get_principal(self, principal_id: int) -> Principal:
        """Build principal model from repository data.

        Args:
            principal_id: Telegram principal identifier.

        Returns:
            Principal with immutable tag set.

        Raises:
            Exception: Propagates storage adapter errors.
        """

        tags = self.principal_tag_repository.get_tags(principal_id)
        logger.debug("Loaded %d tags for principal=%s", len(tags), principal_id)
        return Principal(telegram_id=principal_id, tags=tags)

    def grant_tag(self, principal_id: int, tag: str) -> None:
        """Grant a tag to principal.

        Args:
            principal_id: Telegram principal identifier.
            tag: Tag name to grant.

        Returns:
            None.

        Raises:
            Exception: Propagates storage adapter errors.
        """

        tags = set(self.principal_tag_repository.get_tags(principal_id))
        tags.add(tag)
        self.principal_tag_repository.set_tags(principal_id, frozenset(tags))
        logger.info("Granted tag='%s' to principal=%s", tag, principal_id)

    def revoke_tag(self, principal_id: int, tag: str) -> None:
        """Revoke a tag from principal.

        Args:
            principal_id: Telegram principal identifier.
            tag: Tag name to revoke.

        Returns:
            None.

        Raises:
            Exception: Propagates storage adapter errors.
        """

        tags = set(self.principal_tag_repository.get_tags(principal_id))
        tags.discard(tag)
        self.principal_tag_repository.set_tags(principal_id, frozenset(tags))
        logger.info("Revoked tag='%s' from principal=%s", tag, principal_id)
