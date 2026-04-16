"""Unit tests for ACL bootstrap service."""

from dataclasses import dataclass

from serverbot.application.acl_service import AclService
from serverbot.application.bootstrap_acl import AclBootstrapService
from serverbot.domain.security import PrincipalGrantDescriptor


@dataclass
class InMemoryTagRepository:
    """In-memory principal tag repository for ACL bootstrap tests.

    Args:
        state: Mutable mapping principal id -> tags.
    """

    state: dict[int, frozenset[str]]

    def get_tags(self, principal_id: int) -> frozenset[str]:
        """Get tags by principal id.

        Args:
            principal_id: Telegram principal id.

        Returns:
            Existing immutable tags.

        Raises:
            None.
        """

        return self.state.get(principal_id, frozenset())

    def set_tags(self, principal_id: int, tags: frozenset[str]) -> None:
        """Set tags by principal id.

        Args:
            principal_id: Telegram principal id.
            tags: New immutable tag set.

        Returns:
            None.

        Raises:
            None.
        """

        self.state[principal_id] = tags


def test_acl_bootstrap_applies_all_grants() -> None:
    """Bootstrap should apply each configured grant.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """

    repository = InMemoryTagRepository(state={})
    service = AclBootstrapService(acl_service=AclService(repository))
    grants = (
        PrincipalGrantDescriptor(principal_kind="user", principal_id=1, tag="view.status"),
        PrincipalGrantDescriptor(principal_kind="chat", principal_id=2, tag="view.logs"),
    )

    count = service.apply(grants)

    assert count == 2
    assert repository.state[1] == frozenset({"view.status"})
    assert repository.state[2] == frozenset({"view.logs"})
