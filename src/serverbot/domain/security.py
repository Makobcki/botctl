"""Domain models for ACL bootstrap grants from configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrincipalGrantDescriptor:
    """Grant mapping loaded from configuration.

    Args:
        principal_kind: Principal kind (`user` or `chat`).
        principal_id: Telegram principal identifier.
        tag: ACL tag to grant.
    """

    principal_kind: str
    principal_id: int
    tag: str
