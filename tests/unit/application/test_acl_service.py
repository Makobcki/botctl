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

    def has_principals(self) -> bool:
        """Check if repository already contains ACL principals.

        Args:
            None.

        Returns:
            True when any principal entry exists.
        """

        return bool(self.state)


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


def test_acl_service_bootstrap_first_admin_only_once() -> None:
    """First-admin bootstrap should work once on empty ACL repository.

    Args:
        None.

    Returns:
        None.
    """

    repository = InMemoryPrincipalTagRepository(state={})
    service = AclService(principal_tag_repository=repository)

    first = service.bootstrap_first_admin(100, frozenset({"command.status", "command.acl"}))
    second = service.bootstrap_first_admin(200, frozenset({"command.status"}))

    assert first is True
    assert second is False
    assert service.get_principal(100).tags == frozenset({"command.status", "command.acl"})
