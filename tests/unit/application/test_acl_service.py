"""Unit tests for ACL application service."""

from dataclasses import dataclass

from serverbot.application.acl_service import AclService


@dataclass
class InMemoryPrincipalTagRepository:
    """Minimal in-memory repository for unit tests.

    Args:
        state: Mutable mapping principal -> tags.
    """

    state: dict[int, frozenset[str]]

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Get principal tags from in-memory state.

        Args:
            principal_id: Telegram principal identifier.

        Returns:
            Immutable set of tags.

        Raises:
            None.
        """

        return self.state.get(principal_id, frozenset())

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Set principal tags in in-memory state.

        Args:
            principal_id: Telegram principal identifier.
            tags: New immutable tag set.

        Returns:
            None.

        Raises:
            None.
        """

        self.state[principal_id] = tags


def test_acl_service_grant_and_revoke_tag() -> None:
    """ACL service should modify repository tags predictably.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    repository = InMemoryPrincipalTagRepository(state={})
    service = AclService(principal_tag_repository=repository)

    service.grant_tag(10, "view.status")
    assert service.get_principal(10).tags == frozenset({"view.status"})

    service.revoke_tag(10, "view.status")
    assert service.get_principal(10).tags == frozenset()
