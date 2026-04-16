"""ACL bootstrap service applying grants from configuration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.domain.security import PrincipalGrantDescriptor

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AclBootstrapService:
    """Applies configured ACL grants at startup.

    Args:
        acl_service: ACL service dependency.
    """

    acl_service: AclService

    def apply(self, grants: tuple[PrincipalGrantDescriptor, ...]) -> int:
        """Apply grants and return number of writes performed.

        Args:
            grants: ACL grant descriptors.

        Returns:
            Number of grant operations applied.

        Raises:
            Exception: Propagates underlying storage errors.
        """

        count = 0
        for grant in grants:
            self.acl_service.grant_tag(principal_id=grant.principal_id, tag=grant.tag)
            count += 1
            logger.info(
                "Bootstrap ACL grant applied kind=%s principal=%s tag=%s",
                grant.principal_kind,
                grant.principal_id,
                grant.tag,
            )
        return count
