"""Integration-style test for use-case orchestration."""

import asyncio

from serverbot.application.services import AuditService, PolicyService
from serverbot.application.use_cases import ExecuteCommandUseCase
from serverbot.domain.models import CommandPolicy, Principal


def test_execute_use_case_returns_acl_decision() -> None:
    """Use-case integrates policy and audit and returns decision."""

    use_case = ExecuteCommandUseCase(
        policy_service=PolicyService(
            policies={"status": CommandPolicy(command_name="status", required_tag="view.status")}
        ),
        audit_service=AuditService(),
    )

    decision = asyncio.run(
        use_case.execute(
            principal=Principal(telegram_id=1, tags=frozenset({"view.status"})),
            command_name="status",
        )
    )

    assert decision is True
