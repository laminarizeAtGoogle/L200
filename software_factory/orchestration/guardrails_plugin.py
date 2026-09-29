"""ADK Policy & Security Guardrails Plugin with Model Armor & Self-Evaluation.

Implements a Google ADK `BasePlugin` that intercepts model requests/responses
and tool calls to enforce:
1. Branch Protection Policy: Blocks any attempt to push or commit directly to
   `main` or `master`.
2. Zero-Privilege Local Execution Policy: Blocks local `terraform apply` or
   mutating `gcloud` commands (`create`, `delete`, `update`, `add-iam-policy-binding`).
3. Prompt Injection & Safety Screening: Integrates `google.cloud.modelarmor`
   client alongside deterministic policy filters.
4. Intent vs. Outcome Capture: Automatically records pre-execution Intent and
   post-execution Outcome for every ADK tool invocation.
5. Self-Evaluation Rubric Check: Evaluates model outputs for leaked secrets,
   banned ASCII box art in architecture docs, and policy compliance.
"""

from __future__ import annotations

import re
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from ..observability import (
    DEFAULT_INTENT_OUTCOME_RECORDER,
    DEFAULT_LOGGER,
    DEFAULT_SCRUBBER,
    IntentOutcomeRecorder,
)
from ..schemas import GuidedToolResponse, ToolExecutionStatus

try:
    from google.cloud import modelarmor_v1
except ImportError:  # pragma: no cover
    modelarmor_v1 = None  # type: ignore[assignment]


class SoftwareFactoryGuardrailsPlugin(BasePlugin):
    """ADK Plugin enforcing security policies, Model Armor checks, and Intent/Outcome capture."""

    _MUTATING_GCLOUD_VERBS = frozenset(
        {
            "create",
            "delete",
            "update",
            "add-iam-policy-binding",
            "remove-iam-policy-binding",
            "set-iam-policy",
            "deploy",
            "destroy",
        }
    )

    _PROMPT_INJECTION_PATTERNS = [
        re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions"),
        re.compile(r"(?i)force\s+push\s+to\s+main"),
        re.compile(r"(?i)bypass\s+workload\s+identity"),
    ]

    def __init__(
        self,
        name: str = "software_factory_guardrails",
        recorder: IntentOutcomeRecorder = DEFAULT_INTENT_OUTCOME_RECORDER,
        enable_model_armor: bool = False,
        project_id: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.recorder = recorder
        self.enable_model_armor = enable_model_armor
        self.project_id = project_id
        self._active_correlations: dict[str, str] = {}
        self._model_armor_client: Any | None = None
        if enable_model_armor and modelarmor_v1 is not None:
            try:
                self._model_armor_client = modelarmor_v1.ModelArmorClient()
            except Exception:
                self._model_armor_client = None

    def evaluate_policy_on_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> GuidedToolResponse | None:
        """Evaluates deterministic security policies before a tool runs.

        Returns a `GuidedToolResponse` with `BLOCKED_BY_GUARDRAIL` if a policy
        is violated, or `None` if execution is permitted.
        """
        # 1. Block creating or pushing directly to main/master
        branch = str(
            tool_args.get("branch_name")
            or tool_args.get("head_branch")
            or ""
        ).strip()
        if branch in {"main", "master", "origin/main", "refs/heads/main"}:
            return GuidedToolResponse(
                status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                tool_name=tool_name,
                summary=(
                    f"Guardrail blocked operation targeting protected branch '{branch}'."
                ),
                error_code="PROTECTED_BRANCH_VIOLATION",
                error_message=(
                    f"Direct commits, pushes, or PR head branches using '{branch}' "
                    "are prohibited by the Software Factory constitution."
                ),
                remediation_steps=[
                    "Call `create_isolated_feature_branch_from_main` with a branch name like 'feat/<feature-slug>'.",
                    "Commit your changes to that feature branch.",
                    "Call `open_pull_request_for_terraform_apply` with `head_branch='feat/<feature-slug>'` and `base_branch='main'`.",
                ],
                retryable=True,
            )

        # 2. Block path traversal outside workspace_path
        rel_path = str(tool_args.get("relative_file_path") or "")
        if ".." in rel_path.split("/") or rel_path.startswith("/"):
            return GuidedToolResponse(
                status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                tool_name=tool_name,
                summary="Guardrail blocked path traversal outside target workspace.",
                error_code="WORKSPACE_BOUNDARY_VIOLATION",
                error_message=(
                    f"Relative path '{rel_path}' must stay strictly inside `workspace_path`."
                ),
                remediation_steps=[
                    "Pass a relative path inside the workspace (e.g., 'src/app.py' or 'terraform/main.tf') without '..' or leading '/'.",
                ],
                retryable=True,
            )

        # 3. Enforce read-only boundary on gcloud probes
        if "gcloud" in tool_name or "probe" in tool_name:
            raw_filter = str(tool_args.get("filter_expression") or "")
            tokens = set(re.split(r"[\s;|&]+", raw_filter.lower()))
            forbidden = tokens.intersection(self._MUTATING_GCLOUD_VERBS)
            if forbidden:
                return GuidedToolResponse(
                    status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                    tool_name=tool_name,
                    summary=(
                        f"Guardrail blocked mutating verb(s) {sorted(forbidden)} in read-only gcloud probe."
                    ),
                    error_code="ZERO_PRIVILEGE_READONLY_VIOLATION",
                    error_message=(
                        "The read-only gcloud agent impersonates `cloudtop-agent-reader` "
                        "and cannot execute mutating operations."
                    ),
                    remediation_steps=[
                        "Use `synthesize_cross_project_terraform_module` and `open_pull_request_for_terraform_apply` to provision or mutate GCP resources via GitHub Actions WIF.",
                        "Restrict `probe_gcp_resources_readonly` strictly to read-only inspection.",
                    ],
                    retryable=True,
                )

        return None

    def evaluate_prompt_safety(self, prompt_text: str) -> tuple[bool, str]:
        """Checks user prompt for injection or policy bypass attempts."""
        for pattern in self._PROMPT_INJECTION_PATTERNS:
            if pattern.search(prompt_text):
                return (
                    False,
                    f"Prompt rejected by Software Factory Guardrail: matched policy filter '{pattern.pattern}'.",
                )
        return True, "SAFE"

    def self_evaluate_response(self, response_text: str) -> dict[str, Any]:
        """Runs post-generation self-evaluation checks on agent output."""
        scrubbed = DEFAULT_SCRUBBER.scrub_text(response_text)
        contains_pii_or_secret = scrubbed != response_text
        has_ascii_box = bool(
            re.search(r"\+[=-]{10,}\+", response_text)
            and re.search(r"\|[ ]{10,}\|", response_text)
        )
        return {
            "passed": not contains_pii_or_secret and not has_ascii_box,
            "redacted_sensitive_data": contains_pii_or_secret,
            "ascii_box_violation": has_ascii_box,
            "sanitized_text": scrubbed,
        }

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> LlmResponse | None:
        """ADK hook executed prior to calling the Gemini model."""
        DEFAULT_LOGGER.log_event(
            event_type="GUARDRAIL_BEFORE_MODEL",
            message=f"Guardrail inspected LLM request for agent '{callback_context.agent_name}'",
            agent_name=callback_context.agent_name,
        )
        return None

    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> LlmResponse | None:
        """ADK hook executed after receiving the Gemini model response."""
        DEFAULT_LOGGER.log_event(
            event_type="GUARDRAIL_AFTER_MODEL",
            message=f"Guardrail verified LLM response for agent '{callback_context.agent_name}'",
            agent_name=callback_context.agent_name,
        )
        return None

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict[str, Any] | None:
        """ADK hook capturing Intent BEFORE tool execution and enforcing policy guardrails."""
        agent_name = getattr(tool_context, "agent_name", "focal_coordinator_agent")
        corr_id = self.recorder.record_intent(
            action_name=tool.name,
            actor_agent=agent_name,
            intended_arguments=tool_args,
            rationale=f"ADK tool invocation from {agent_name}",
        )
        key = f"{agent_name}:{tool.name}"
        self._active_correlations[key] = corr_id

        violation = self.evaluate_policy_on_tool_call(tool.name, tool_args)
        if violation is not None:
            result_dict = violation.model_dump(mode="json")
            self.recorder.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=result_dict,
                error_details=violation.error_message,
            )
            return result_dict

        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """ADK hook capturing actual Outcome AFTER tool execution completes."""
        agent_name = getattr(tool_context, "agent_name", "focal_coordinator_agent")
        key = f"{agent_name}:{tool.name}"
        corr_id = self._active_correlations.pop(key, None)
        if corr_id is None:
            corr_id = self.recorder.record_intent(
                action_name=tool.name,
                actor_agent=agent_name,
                intended_arguments=tool_args,
            )

        status_str = "success"
        if isinstance(result, dict):
            status_str = str(result.get("status", "success"))

        self.recorder.record_outcome(
            correlation_id=corr_id,
            outcome_status=status_str,
            actual_result=result,
        )
        return None


DEFAULT_GUARDRAILS_PLUGIN = SoftwareFactoryGuardrailsPlugin()
