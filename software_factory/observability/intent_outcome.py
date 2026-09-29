"""Intent vs. Outcome audit capture for agent and tool executions.

Explicitly logs the agent's *intended* action (tool name, arguments, rationale,
correlation ID) BEFORE execution and the *actual* outcome (status, latency_ms,
result summary, error details) AFTER execution.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .structured_logging import DEFAULT_LOGGER, StructuredJsonLogger
from .telemetry import DEFAULT_TELEMETRY, TelemetryManager


class IntentOutcomeRecorder:
    """Captures paired Intent (pre-execution) and Outcome (post-execution) events."""

    def __init__(
        self,
        logger: StructuredJsonLogger = DEFAULT_LOGGER,
        telemetry: TelemetryManager = DEFAULT_TELEMETRY,
    ) -> None:
        self.logger = logger
        self.telemetry = telemetry
        self._in_flight: dict[str, dict[str, Any]] = {}
        self.audit_trail: list[dict[str, Any]] = []

    def record_intent(
        self,
        *,
        action_name: str,
        actor_agent: str,
        intended_arguments: dict[str, Any],
        rationale: str = "Agent selected tool to satisfy user intent",
        session_id: str | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Records the agent's intended action BEFORE execution begins."""
        corr_id = correlation_id or str(uuid.uuid4())
        started_at = time.monotonic()

        intent_record = self.logger.log_event(
            event_type="AGENT_ACTION_INTENT",
            message=f"Intent: {actor_agent} preparing to execute '{action_name}'",
            severity="INFO",
            agent_name=actor_agent,
            session_id=session_id,
            metadata={
                "phase": "INTENT_BEFORE_EXECUTION",
                "correlation_id": corr_id,
                "action_name": action_name,
                "rationale": rationale,
                "intended_arguments": intended_arguments,
            },
        )
        self._in_flight[corr_id] = {
            "started_at": started_at,
            "action_name": action_name,
            "actor_agent": actor_agent,
            "session_id": session_id,
            "intent_record": intent_record,
        }
        self.audit_trail.append(intent_record)
        return corr_id

    def record_outcome(
        self,
        *,
        correlation_id: str,
        outcome_status: str,
        actual_result: Any,
        error_details: str | None = None,
    ) -> dict[str, Any]:
        """Records the actual outcome AFTER execution finishes."""
        inflight = self._in_flight.pop(correlation_id, {})
        started_at = inflight.get("started_at", time.monotonic())
        latency_ms = round((time.monotonic() - started_at) * 1000.0, 2)
        action_name = inflight.get("action_name", "unknown_action")
        actor_agent = inflight.get("actor_agent", "focal_coordinator_agent")
        session_id = inflight.get("session_id")

        severity = "INFO" if outcome_status == "success" else "WARNING"
        outcome_record = self.logger.log_event(
            event_type="AGENT_ACTION_OUTCOME",
            message=(
                f"Outcome: {actor_agent} completed '{action_name}' "
                f"with status='{outcome_status}' in {latency_ms}ms"
            ),
            severity=severity,
            agent_name=actor_agent,
            session_id=session_id,
            metadata={
                "phase": "OUTCOME_AFTER_EXECUTION",
                "correlation_id": correlation_id,
                "action_name": action_name,
                "outcome_status": outcome_status,
                "latency_ms": latency_ms,
                "actual_result": actual_result,
                "error_details": error_details,
            },
        )
        self.audit_trail.append(outcome_record)
        return outcome_record


DEFAULT_INTENT_OUTCOME_RECORDER = IntentOutcomeRecorder()
