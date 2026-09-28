"""Human-in-the-Loop (HITL) confirmation hooks for high-stakes actions.

Implements explicit code stops requiring human confirmation before executing
high-stakes operations:
- Merging Pull Requests to `main` (which triggers `terraform apply`)
- Applying live cross-project Workload Identity Federation IAM bindings
- Destructive infrastructure or filesystem mutations
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from google.adk.tools.tool_confirmation import ToolConfirmation

from ..observability import DEFAULT_LOGGER


class HumanInTheLoopGate:
    """Manages pending human approval tickets and enforces explicit code stops."""

    HIGH_STAKES_ACTIONS = frozenset(
        {
            "merge_pull_request_terraform_apply",
            "cross_project_wif_iam_binding",
            "destructive_resource_change",
        }
    )

    def __init__(self) -> None:
        self._tickets: dict[str, dict[str, Any]] = {}

    def create_approval_request(
        self,
        *,
        action_type: str,
        target_workspace: str,
        target_project_id: str,
        proposed_command_or_diff: str,
        risk_assessment: str,
        session_id: str = "default-session",
    ) -> dict[str, Any]:
        """Creates a pending HITL approval ticket and halts immediate execution."""
        approval_id = f"hitl-{uuid.uuid4().hex[:12]}"
        adk_confirmation = ToolConfirmation(
            hint=(
                f"Human confirmation required for '{action_type}' on project "
                f"'{target_project_id}' ({target_workspace})."
            ),
            confirmed=False,
            payload={
                "approval_id": approval_id,
                "action_type": action_type,
                "target_workspace": target_workspace,
                "target_project_id": target_project_id,
            },
        )
        ticket: dict[str, Any] = {
            "approval_id": approval_id,
            "status": "pending",
            "action_type": action_type,
            "target_workspace": target_workspace,
            "target_project_id": target_project_id,
            "proposed_command_or_diff": proposed_command_or_diff,
            "risk_assessment": risk_assessment,
            "session_id": session_id,
            "adk_tool_confirmation": adk_confirmation.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "resolved_by": None,
            "reviewer_comment": None,
        }
        self._tickets[approval_id] = ticket

        DEFAULT_LOGGER.log_event(
            event_type="HITL_APPROVAL_REQUESTED",
            message=(
                f"Human-in-the-Loop confirmation required: {approval_id} "
                f"for '{action_type}' on '{target_project_id}'"
            ),
            severity="WARNING",
            session_id=session_id,
            workspace_path=target_workspace,
            metadata=ticket,
        )
        return ticket

    def resolve_approval(
        self,
        approval_id: str,
        *,
        approved: bool,
        reviewer: str = "human-operator",
        comment: str = "",
    ) -> dict[str, Any]:
        """Approves or rejects a pending Human-in-the-Loop ticket."""
        ticket = self._tickets.get(approval_id)
        if not ticket:
            raise KeyError(f"Approval ticket '{approval_id}' not found.")

        ticket["status"] = "approved" if approved else "rejected"
        ticket["resolved_at"] = datetime.now(timezone.utc).isoformat()
        ticket["resolved_by"] = reviewer
        ticket["reviewer_comment"] = comment
        ticket["adk_tool_confirmation"]["confirmed"] = approved

        DEFAULT_LOGGER.log_event(
            event_type="HITL_APPROVAL_RESOLVED",
            message=(
                f"HITL ticket '{approval_id}' {ticket['status']} by '{reviewer}'"
            ),
            session_id=ticket.get("session_id"),
            workspace_path=ticket.get("target_workspace"),
            metadata={
                "approval_id": approval_id,
                "status": ticket["status"],
                "reviewer": reviewer,
                "comment": comment,
            },
        )
        return ticket

    def is_approved(self, approval_id: str | None) -> bool:
        """Returns True only if the provided approval_id exists and was explicitly approved."""
        if not approval_id:
            return False
        ticket = self._tickets.get(approval_id)
        return bool(ticket and ticket.get("status") == "approved")

    def list_pending_approvals(
        self, session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Lists all pending approval requests, optionally filtered by session_id."""
        results = [
            t
            for t in self._tickets.values()
            if t.get("status") == "pending"
            and (session_id is None or t.get("session_id") == session_id)
        ]
        return results

    def get_ticket(self, approval_id: str) -> dict[str, Any] | None:
        """Retrieves a specific approval ticket by ID."""
        return self._tickets.get(approval_id)


DEFAULT_HITL_GATE = HumanInTheLoopGate()
