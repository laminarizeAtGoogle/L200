"""Strict Database Access Restriction Guardrail.

Enforces the enterprise security policy:
- The agent is strictly read-only for cloud infrastructure resources and Cloud Logging.
- Querying internal application databases (Cloud SQL, Spanner, Firestore, Bigtable,
  BigQuery dataset contents) is strictly forbidden and blocked before execution.
- Only Cloud Logging systems are permitted for diagnostic and audit inspection.
"""

from __future__ import annotations

import re
from typing import Any

from ..observability import DEFAULT_LOGGER, DEFAULT_TELEMETRY
from ..schemas import GuidedToolResponse, ToolExecutionStatus


# Patterns targeting direct querying of internal databases
_DATABASE_QUERY_PATTERNS = [
    re.compile(r"\b(?:select\s+.+\s+from|insert\s+into|update\s+.+\s+set|delete\s+from)\b", re.IGNORECASE),
    re.compile(r"\b(?:cloud\s*sql|cloudsql|postgres|postgresql|mysql)\b.*\b(?:query|table|records|database|select|dump)\b", re.IGNORECASE),
    re.compile(r"\b(?:query|show|inspect|list|dump)\b.*\b(?:tables?|rows?|columns?|records?|schema)\b.*\b(?:database|sql|spanner|firestore|bigtable)\b", re.IGNORECASE),
    re.compile(r"\b(?:spanner|firestore|bigtable|datastore)\b.*\b(?:query|records?|documents?|collections?|data)\b", re.IGNORECASE),
    re.compile(r"\b(?:bq\s+query|bigquery\s+query|select\s+\*\s+from)\b", re.IGNORECASE),
]

# Patterns explicitly recognizing allowed logging and telemetry queries
_ALLOWED_LOGGING_PATTERNS = [
    re.compile(r"\b(?:cloud\s*logging|logs?|stackdriver|audit\s*logs?|syslog|stderr|stdout)\b", re.IGNORECASE),
    re.compile(r"\b(?:error\s*logs?|crash\s*logs?|request\s*logs?)\b", re.IGNORECASE),
]


class DatabaseAccessBlockerGuardrail:
    """Security guardrail intercepting and denying any attempt to query internal databases."""

    def __init__(self) -> None:
        self.policy_name = "STRICT_DATABASE_QUERY_RESTRICTION"

    def check_query_allowed(self, user_intent: str) -> tuple[bool, str, list[str]]:
        """Evaluates whether the user query complies with the database isolation policy.

        Returns:
            (is_allowed, reason, remediation_steps)
        """
        with DEFAULT_TELEMETRY.start_span("guardrails.check_database_access"):
            clean_intent = user_intent.strip()

            # Check if query specifically targets logging systems (allowed exception)
            is_logging_query = any(pattern.search(clean_intent) for pattern in _ALLOWED_LOGGING_PATTERNS)
            if is_logging_query and not re.search(r"\b(?:select\s+.+\s+from)\b", clean_intent, re.IGNORECASE):
                return True, "Cloud Logging queries are explicitly permitted.", []

            # Check for forbidden database query attempts
            for pattern in _DATABASE_QUERY_PATTERNS:
                if pattern.search(clean_intent):
                    DEFAULT_LOGGER.log_event(
                        event_type="DATABASE_ACCESS_ATTEMPT_BLOCKED",
                        message="User or agent query attempted internal database inspection",
                        metadata={
                            "matched_pattern": pattern.pattern,
                            "intent_sample": clean_intent[:120],
                        },
                    )
                    return (
                        False,
                        "Direct querying of internal application databases (Cloud SQL, Spanner, Firestore, "
                        "Bigtable, BigQuery) is strictly prohibited by enterprise security policy. "
                        "This agent is only authorized to inspect cloud infrastructure state and Cloud Logging systems.",
                        [
                            "Query Google Cloud infrastructure resources (Compute Engine VMs, Cloud Run services, GKE clusters, Cloud Storage metadata).",
                            "Query Cloud Logging systems (query_cloud_logging_readonly) to inspect database error logs, connection errors, or audit trails.",
                            "Do not attempt to execute SQL commands or read internal application database tables.",
                        ],
                    )

            return True, "Query complies with cloud environment read-only policies.", []

    def create_blocked_response(
        self,
        reason: str,
        remediation_steps: list[str],
    ) -> GuidedToolResponse:
        """Constructs a standardized GuidedToolResponse for blocked database operations."""
        return GuidedToolResponse(
            status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
            tool_name="database_access_guardrail",
            summary="Operation blocked: Querying application databases is prohibited.",
            error_code="POLICY_DATABASE_ACCESS_FORBIDDEN",
            error_message=reason,
            remediation_steps=remediation_steps,
            retryable=False,
            data={"policy": self.policy_name, "databases_permitted": False, "logging_permitted": True},
        )


DEFAULT_DATABASE_GUARDRAIL = DatabaseAccessBlockerGuardrail()
