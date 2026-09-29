"""Focal Conversational Coordinator Agent and ADK App Definition.

Serves as the single conversational focal point between the user and the A2A
Software Factory agent graph:
- Translates user intent into coordinated actions across specialist sub-agents
  (`workspace_architect_agent`, `software_builder_agent`,
  `wif_git_delivery_agent`, `gcloud_readonly_probe_agent`,
  `software_delivery_pipeline`, and `parallel_verification_agent`).
- Communicates workspace, branch, WIF, Pull Request, and GCP verification state
  back to the user.
- Wraps the graph in an ADK `App` configured with `SoftwareFactoryGuardrailsPlugin`,
  `EventsCompactionConfig`, and `ContextCacheConfig`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.tools import load_memory, preload_memory

from ..audio import DEFAULT_TTS_SERVICE
from ..config import DEFAULT_CONFIG, WORKSPACE_ROOT, FactoryConfig
from ..memory import (
    DEFAULT_ASYNC_CONSOLIDATOR,
    DEFAULT_COMPACTOR,
    DEFAULT_MEMORY_STORE,
    build_adk_context_cache_config,
    build_adk_events_compaction_config,
)
from ..observability import (
    DEFAULT_LOGGER,
    DEFAULT_SCRUBBER,
    DEFAULT_TELEMETRY,
)
from ..orchestration import (
    DEFAULT_GUARDRAILS_PLUGIN,
    DEFAULT_HITL_GATE,
    DEFAULT_MODEL_ROUTER,
)
from ..orchestration.database_guardrail import DEFAULT_DATABASE_GUARDRAIL
from ..prompts import (
    FOCAL_COORDINATOR_CONSTITUTION,
    GEMINI_ENTERPRISE_CLOUD_CHAT_CONSTITUTION,
)
from ..schemas import (
    AgentStateSummary,
    ChatMessageRequest,
    ChatMessageResponse,
    CloudChatRequest,
    CloudChatResponse,
    IapUserIdentity,
    TtsSynthesisRequest,
)
from ..tools import (
    ALL_FACTORY_TOOLS,
    configure_cross_project_wif_federation,
    create_isolated_feature_branch_from_main,
    generate_workspace_software_artifact,
    inspect_target_workspace_state,
    open_pull_request_for_terraform_apply,
    probe_gcp_resources_readonly,
    query_cloud_logging_entries_readonly,
    query_cloud_logging_readonly,
    query_cloud_run_services_readonly,
    query_compute_instances_readonly,
    query_iam_policy_readonly,
    query_storage_buckets_readonly,
    request_human_approval_for_high_stakes_action,
    synthesize_cross_project_terraform_module,
    verify_deployed_argolis_infrastructure,
)
from .subagents import (
    build_gcloud_readonly_probe_agent,
    build_parallel_verification_agent,
    build_software_builder_agent,
    build_software_delivery_sequential_pipeline,
    build_wif_git_delivery_agent,
    build_workspace_architect_agent,
)


def build_focal_coordinator_agent(
    name: str = "focal_coordinator_agent",
) -> LlmAgent:
    """Constructs the root Focal Conversational Coordinator LlmAgent."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(name)
    return LlmAgent(
        name=name,
        model=routing.selected_model,
        description=(
            "Single conversational focal point for the A2A Software Factory. "
            "Communicates state from specialist agents to the user and translates "
            "user intent into software builds, cross-project WIF onboarding, "
            "feature-branch PRs, and read-only gcloud verification."
        ),
        instruction=FOCAL_COORDINATOR_CONSTITUTION,
        tools=[
            *ALL_FACTORY_TOOLS,
            load_memory,
            preload_memory,
        ],
        sub_agents=[
            build_workspace_architect_agent(),
            build_software_builder_agent(),
            build_wif_git_delivery_agent(),
            build_gcloud_readonly_probe_agent(),
            build_software_delivery_sequential_pipeline(),
            build_parallel_verification_agent(),
        ],
    )


def build_software_factory_adk_app(
    config: FactoryConfig = DEFAULT_CONFIG,
) -> App:
    """Creates the complete Google ADK `App` with guardrails, compaction, and caching."""
    root_agent = build_focal_coordinator_agent()
    return App(
        name=config.app_name,
        root_agent=root_agent,
        plugins=[DEFAULT_GUARDRAILS_PLUGIN],
        events_compaction_config=build_adk_events_compaction_config(config),
        context_cache_config=build_adk_context_cache_config(),
    )


class FocalConversationOrchestrator:
    """Executes conversational intents through the Focal Coordinator and specialist tools.

    Maintains persistent session/workspace state, applies prompt guardrails,
    compacts history, dispatches to the appropriate specialist sub-agents/tools,
    and schedules non-blocking background memory consolidation.
    """

    def __init__(self, config: FactoryConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.session_turns: dict[str, list[dict[str, Any]]] = {}

    async def handle_chat(
        self,
        request: ChatMessageRequest,
        a2a_endpoints: dict[str, str],
    ) -> ChatMessageResponse:
        """Processes a user message at the single conversational focal point."""
        with DEFAULT_TELEMETRY.start_span(
            "focal_coordinator.handle_chat",
            attributes={
                "session_id": request.session_id,
                "user_id": request.user_id,
                "workspace_path": request.workspace_path or str(WORKSPACE_ROOT),
            },
        ):
            trace_id, _ = DEFAULT_TELEMETRY.get_current_trace_context()

            # 1. Resolve persisted session state
            existing_state = DEFAULT_MEMORY_STORE.get_session_workspace_state(
                request.session_id
            )
            workspace_path = str(
                Path(
                    request.workspace_path
                    or (existing_state or {}).get("workspace_path")
                    or WORKSPACE_ROOT
                )
                .expanduser()
                .resolve()
            )
            target_project = (
                request.target_gcp_project_id
                or (existing_state or {}).get("target_gcp_project")
                or self.config.project_id
            )
            target_repo = (
                request.target_github_repo
                or (existing_state or {}).get("target_github_repo")
                or "laminarizeAtGoogle/L200"
            )

            # 2. Check Prompt Safety Guardrail
            is_safe, safety_reason = (
                DEFAULT_GUARDRAILS_PLUGIN.evaluate_prompt_safety(
                    request.message
                )
            )
            routing = DEFAULT_MODEL_ROUTER.route_user_intent(request.message)

            if not is_safe:
                state_summary = AgentStateSummary(
                    active_agent="focal_coordinator_agent",
                    routed_model=routing.selected_model,
                    active_workspace=workspace_path,
                    active_branch=(existing_state or {}).get("active_branch"),
                    target_gcp_project=target_project,
                    pending_approvals=DEFAULT_HITL_GATE.list_pending_approvals(
                        request.session_id
                    ),
                    invoked_subagents=[],
                    tool_executions=[
                        {
                            "status": "blocked_by_guardrail",
                            "reason": safety_reason,
                        }
                    ],
                    trace_id=trace_id,
                )
                return ChatMessageResponse(
                    session_id=request.session_id,
                    reply=safety_reason,
                    state=state_summary,
                    a2a_endpoints=a2a_endpoints,
                )

            # 3. Append user turn & run sliding-window History Compaction
            turns = self.session_turns.setdefault(request.session_id, [])
            turns.append({"role": "user", "content": request.message})
            compaction_result = DEFAULT_COMPACTOR.compact_turns(
                turns, session_id=request.session_id
            )
            if compaction_result["compacted"]:
                self.session_turns[request.session_id] = list(
                    compaction_result["active_turns"]
                )

            # 4. Orchestrate specialist sub-agents & tools based on user intent
            lower_msg = request.message.lower()
            invoked_subagents: list[str] = []
            tool_executions: list[dict[str, Any]] = []
            reply_sections: list[str] = []

            # Always inspect workspace state to ground the coordinator
            invoked_subagents.append("workspace_architect_agent")
            ws_info = inspect_target_workspace_state(
                workspace_path=workspace_path,
                include_git_status=True,
                max_files=50,
            )
            tool_executions.append(ws_info)
            active_branch = ws_info.get("data", {}).get("active_branch")

            # Enforce policy if user asks to push directly to main
            if "push" in lower_msg and "main" in lower_msg and "branch" not in lower_msg and "pr" not in lower_msg:
                blocked = DEFAULT_GUARDRAILS_PLUGIN.evaluate_policy_on_tool_call(
                    "create_isolated_feature_branch_from_main",
                    {"branch_name": "main", "workspace_path": workspace_path},
                )
                if blocked:
                    blocked_dict = blocked.model_dump(mode="json")
                    tool_executions.append(blocked_dict)
                    reply_sections.append(
                        f"### Guardrail Policy Enforcement\n"
                        f"- **Blocked**: {blocked.error_message}\n"
                        f"- **Remediation**: {' '.join(blocked.remediation_steps)}"
                    )

            # WIF cross-project onboarding intent
            if any(k in lower_msg for k in ("wif", "onboard", "workload identity", "federation", "outside")):
                invoked_subagents.append("wif_git_delivery_agent")
                wif_res = configure_cross_project_wif_federation(
                    workspace_path=workspace_path,
                    target_gcp_project_id=target_project,
                    github_repo=target_repo,
                    dry_run=True,
                )
                tool_executions.append(wif_res)
                reply_sections.append(
                    f"### Cross-Project WIF Onboarding (`wif_git_delivery_agent`)\n"
                    f"- {wif_res.get('summary')}\n"
                    f"- **State Bucket**: `gs://{wif_res.get('data', {}).get('tf_state_bucket')}`\n"
                    f"- **Deployer SA**: `{wif_res.get('data', {}).get('deployer_service_account')}`"
                )

            # Terraform / IaC synthesis intent
            if any(k in lower_msg for k in ("terraform", "iac", "stand up", "provision")):
                invoked_subagents.append("software_builder_agent")
                verify_res = verify_deployed_argolis_infrastructure(
                    project_id=target_project,
                    expected_resources=[
                        "github-terraform-deployer",
                        "cloudtop-agent-reader",
                        "tfstate",
                    ],
                    workspace_path=workspace_path,
                )
                tool_executions.append(verify_res)
                reply_sections.append(
                    f"### Infrastructure & Terraform Verification (`software_builder_agent`)\n"
                    f"- {verify_res.get('summary')}\n"
                    f"- **Workflow**: Changes are authored on a feature branch (`{active_branch or 'factory/v1'}`) and applied via GitHub Actions PR to `main`."
                )

            # Read-only gcloud probe / log inspection intent
            if any(k in lower_msg for k in ("probe", "gcloud", "log", "verify", "resource", "check", "status")):
                invoked_subagents.append("gcloud_readonly_probe_agent")
                probe_res = probe_gcp_resources_readonly(
                    project_id=target_project,
                    resource_domain="service_accounts",
                )
                tool_executions.append(probe_res)
                reply_sections.append(
                    f"### Read-Only GCP Probe (`gcloud_readonly_probe_agent`)\n"
                    f"- {probe_res.get('summary')}\n"
                    f"- **Impersonated SA**: `cloudtop-agent-reader@{target_project}.iam.gserviceaccount.com`"
                )

            # High-stakes merge / apply intent -> trigger HITL gate
            if any(k in lower_msg for k in ("merge", "apply now", "destroy", "delete")):
                invoked_subagents.append("wif_git_delivery_agent")
                hitl_res = request_human_approval_for_high_stakes_action(
                    action_type="merge_pull_request_terraform_apply",
                    target_workspace=workspace_path,
                    target_project_id=target_project,
                    proposed_command_or_diff=(
                        f"Merge feature branch '{active_branch or 'factory/v1'}' -> 'main' "
                        f"to trigger WIF terraform apply on '{target_project}'"
                    ),
                    risk_assessment=(
                        "Triggers automated `terraform apply` via GitHub Actions OIDC WIF."
                    ),
                )
                tool_executions.append(hitl_res)
                reply_sections.append(
                    f"### Human-in-the-Loop Gate Triggered\n"
                    f"- {hitl_res.get('summary')}\n"
                    f"- Approve via `POST /api/v1/approvals/{hitl_res.get('data', {}).get('approval_id')}`."
                )

            if not reply_sections:
                reply_sections.append(
                    f"### Focal Coordinator State Summary\n"
                    f"- **Active Workspace**: `{workspace_path}` (branch `{active_branch}`)\n"
                    f"- **Target GCP Project**: `{target_project}` (Repo: `{target_repo}`)\n"
                    f"- **Routed Model**: `{routing.selected_model}` ({routing.complexity_tier})\n"
                    f"- **Specialist A2A Graph Ready**: `workspace_architect_agent`, `software_builder_agent`, `wif_git_delivery_agent`, and `gcloud_readonly_probe_agent`."
                )

            raw_reply = "\n\n".join(reply_sections)
            self_eval = DEFAULT_GUARDRAILS_PLUGIN.self_evaluate_response(
                raw_reply
            )
            final_reply = self_eval["sanitized_text"]

            self.session_turns[request.session_id].append(
                {"role": "assistant", "content": final_reply}
            )

            # 5. Persist workspace state & schedule non-blocking async memory consolidation
            DEFAULT_MEMORY_STORE.upsert_session_workspace_state(
                session_id=request.session_id,
                user_id=request.user_id,
                workspace_path=workspace_path,
                target_gcp_project=target_project,
                active_branch=active_branch,
                target_github_repo=target_repo,
                state={
                    "last_model": routing.selected_model,
                    "invoked_subagents": invoked_subagents,
                },
            )
            DEFAULT_ASYNC_CONSOLIDATOR.schedule_turn_consolidation(
                session_id=request.session_id,
                user_id=request.user_id,
                user_message=request.message,
                agent_reply=final_reply,
                workspace_path=workspace_path,
                metadata={
                    "target_gcp_project": target_project,
                    "routed_model": routing.selected_model,
                    "invoked_subagents": invoked_subagents,
                },
            )

            state_summary = AgentStateSummary(
                active_agent="focal_coordinator_agent",
                routed_model=routing.selected_model,
                active_workspace=workspace_path,
                active_branch=active_branch,
                target_gcp_project=target_project,
                pending_approvals=DEFAULT_HITL_GATE.list_pending_approvals(
                    request.session_id
                ),
                invoked_subagents=invoked_subagents,
                tool_executions=tool_executions,
                trace_id=trace_id,
            )

            DEFAULT_LOGGER.log_event(
                event_type="FOCAL_CHAT_TURN_COMPLETED",
                message=f"Completed conversational turn for session '{request.session_id}'",
                session_id=request.session_id,
                workspace_path=workspace_path,
                metadata={
                    "routed_model": routing.selected_model,
                    "invoked_subagents": invoked_subagents,
                    "tool_count": len(tool_executions),
                },
            )

            return ChatMessageResponse(
                session_id=request.session_id,
                reply=DEFAULT_SCRUBBER.scrub_text(final_reply),
                state=state_summary,
                a2a_endpoints=a2a_endpoints,
            )

    async def handle_cloud_chat(
        self,
        request: CloudChatRequest,
        authenticated_user: IapUserIdentity,
    ) -> CloudChatResponse:
        """Handles a conversational turn from the Gemini Enterprise frontend.

        Enforces:
        - Strict database access quarantine (Cloud SQL, Spanner, Firestore, Bigtable, BigQuery)
        - Least-privilege read-only cloud infrastructure inspection
        - Multi-turn sliding window memory compaction
        - Cloud Text-to-Speech (TTS) voice response synthesis
        - Real-time OpenTelemetry distributed tracing and structured JSON logging
        """
        with DEFAULT_TELEMETRY.start_span(
            "cloud_chat.orchestrate",
            attributes={
                "user_email": authenticated_user.email,
                "session_id": request.session_id,
                "enable_tts": request.enable_tts,
            },
        ) as span:
            raw_tid = span.get_span_context().trace_id if span else None
            trace_id = (
                f"{raw_tid:032x}"
                if isinstance(raw_tid, int)
                else (str(raw_tid) if raw_tid else None)
            )
            project_id = request.target_project_id or self.config.project_id
            user_msg = request.message.strip()

            DEFAULT_LOGGER.log_event(
                event_type="CLOUD_CHAT_TURN_STARTED",
                message=f"Received query from IAP user '{authenticated_user.email}'",
                session_id=request.session_id,
                metadata={
                    "user_email": authenticated_user.email,
                    "target_project": project_id,
                    "enable_tts": request.enable_tts,
                },
            )

            # 1. Evaluate Strict Database Access Quarantine Guardrail
            is_allowed, denial_reason, remediation_steps = (
                DEFAULT_DATABASE_GUARDRAIL.check_query_allowed(user_msg)
            )
            if not is_allowed:
                refusal_reply = (
                    f"### 🛡️ Enterprise Security Policy Refusal\n\n"
                    f"**Action Blocked:** {denial_reason}\n\n"
                    f"**Permitted Actions:**\n"
                    + "\n".join(f"- {step}" for step in remediation_steps)
                )

                audio_b64 = None
                if request.enable_tts:
                    tts_res = await DEFAULT_TTS_SERVICE.synthesize(
                        TtsSynthesisRequest(
                            text="Access to internal application databases is restricted by enterprise policy. You can query cloud infrastructure resources or inspect Cloud Logging systems instead.",
                            voice_name=request.voice_name,
                        )
                    )
                    audio_b64 = tts_res.audio_base64

                return CloudChatResponse(
                    session_id=request.session_id,
                    reply=refusal_reply,
                    audio_base64=audio_b64,
                    user_email=authenticated_user.email,
                    model_used=self.config.primary_chat_model,
                    resource_queries_executed=[],
                    database_blocked=True,
                    trace_id=trace_id,
                )

            # 2. Strategic Model Routing (Gemini 3.8 Flash vs Gemini 3.8 Pro)
            routing = DEFAULT_MODEL_ROUTER.route_user_intent(user_msg)

            # 3. Dynamic Context & Turn Compaction
            turns = self.session_turns.setdefault(request.session_id, [])
            turns.append({"role": "user", "content": user_msg})
            compaction_res = DEFAULT_COMPACTOR.compact_turns(
                turns, session_id=request.session_id
            )
            if compaction_res.get("compacted"):
                self.session_turns[request.session_id] = list(
                    compaction_res["active_turns"]
                )

            # 4. Dispatch Read-Only Cloud Inspection Tools
            lower_msg = user_msg.lower()
            executed_tools: list[str] = []
            reply_sections: list[str] = []

            # Compute VM check
            if any(k in lower_msg for k in ("compute", "vm", "instance", "server")):
                executed_tools.append("query_compute_instances_readonly")
                comp_res = query_compute_instances_readonly({"project_id": project_id})
                reply_sections.append(
                    f"### 🖥️ Compute Engine VM Instances\n"
                    f"- {comp_res.get('summary')}\n"
                    f"- **Project**: `{project_id}`\n"
                    f"- **Inspection SA**: `{self.config.readonly_service_account}`"
                )

            # Cloud Run services check
            if any(k in lower_msg for k in ("run", "service", "revision", "container", "endpoint")):
                executed_tools.append("query_cloud_run_services_readonly")
                run_res = query_cloud_run_services_readonly({"project_id": project_id})
                reply_sections.append(
                    f"### ⚡ Cloud Run Services\n"
                    f"- {run_res.get('summary')}\n"
                    f"- **Status**: Monitored via Cloud Run v2 Admin API (read-only)."
                )

            # Storage buckets check
            if any(k in lower_msg for k in ("bucket", "storage", "gcs")):
                executed_tools.append("query_storage_buckets_readonly")
                gcs_res = query_storage_buckets_readonly({"project_id": project_id})
                reply_sections.append(
                    f"### 🪣 Cloud Storage Buckets\n"
                    f"- {gcs_res.get('summary')}\n"
                    f"- **Security Constraint**: Bucket metadata only; customer object payloads are isolated."
                )

            # IAM roles check
            if any(k in lower_msg for k in ("iam", "role", "permission", "service account", "principal")):
                executed_tools.append("query_iam_policy_readonly")
                iam_res = query_iam_policy_readonly({"project_id": project_id})
                reply_sections.append(
                    f"### 🔐 IAM Policy & Role Bindings\n"
                    f"- {iam_res.get('summary')}\n"
                    f"- **Caller Identity**: `{authenticated_user.email}` (Role: `roles/iap.httpsResourceAccessor`)"
                )

            # Cloud Logging check
            if any(k in lower_msg for k in ("log", "logging", "error", "trace", "stackdriver", "audit")):
                executed_tools.append("query_cloud_logging_readonly")
                severity = "ERROR" if "error" in lower_msg else "DEFAULT"
                log_res = query_cloud_logging_readonly(
                    {"severity": severity, "max_entries": 10, "target_project_id": project_id}
                )
                reply_sections.append(
                    f"### 📋 Cloud Logging Inspection\n"
                    f"- {log_res.get('summary')}\n"
                    f"- **Severity Filter**: `{severity}`\n"
                    f"- **Audit Scope**: Project `{project_id}`"
                )

            # Default environment synthesis if no single tool matched
            if not reply_sections:
                executed_tools.append("probe_gcp_resources_readonly")
                probe_res = probe_gcp_resources_readonly(
                    {"resource_domain": "service_accounts", "target_project_id": project_id}
                )
                reply_sections.append(
                    f"### ✦ Cloud Infrastructure Summary\n\n"
                    f"Hello **{authenticated_user.email}**. I have verified your Google Cloud environment in project `{project_id}`:\n\n"
                    f"- **Model**: `{routing.selected_model}` ({routing.complexity_tier})\n"
                    f"- **Environment Access**: Strictly read-only (`{self.config.readonly_service_account}`)\n"
                    f"- **Application Database Guardrail**: Active (Direct SQL/Spanner/Firestore querying blocked)\n"
                    f"- **Cloud Logging**: Ready for diagnostic trace inspection\n\n"
                    f"You can ask me to list Compute VMs, Cloud Run services, inspect IAM role bindings, or query Cloud Logging for recent system errors."
                )

            raw_reply = "\n\n".join(reply_sections)
            sanitized_reply = DEFAULT_SCRUBBER.scrub_text(raw_reply)

            # Save turn in memory
            self.session_turns[request.session_id].append(
                {"role": "assistant", "content": sanitized_reply}
            )

            # 5. Text-to-Speech (TTS) Voice Synthesis
            audio_base64 = None
            if request.enable_tts:
                tts_res = await DEFAULT_TTS_SERVICE.synthesize(
                    TtsSynthesisRequest(
                        text=sanitized_reply,
                        voice_name=request.voice_name or self.config.tts_voice_name,
                    )
                )
                audio_base64 = tts_res.audio_base64

            # 6. Schedule non-blocking async memory consolidation
            DEFAULT_ASYNC_CONSOLIDATOR.schedule_turn_consolidation(
                session_id=request.session_id,
                user_id=authenticated_user.email,
                user_message=user_msg,
                agent_reply=sanitized_reply,
                workspace_path=str(WORKSPACE_ROOT),
                metadata={
                    "target_gcp_project": project_id,
                    "routed_model": routing.selected_model,
                    "executed_tools": executed_tools,
                    "user_email": authenticated_user.email,
                },
            )

            DEFAULT_LOGGER.log_event(
                event_type="CLOUD_CHAT_TURN_COMPLETED",
                message=f"Completed Cloud Chat turn for user '{authenticated_user.email}'",
                session_id=request.session_id,
                metadata={
                    "model_used": routing.selected_model,
                    "executed_tools": executed_tools,
                    "tts_generated": bool(audio_base64),
                },
            )

            return CloudChatResponse(
                session_id=request.session_id,
                reply=sanitized_reply,
                audio_base64=audio_base64,
                audio_content_type="audio/mp3",
                user_email=authenticated_user.email,
                model_used=routing.selected_model,
                resource_queries_executed=executed_tools,
                database_blocked=False,
                trace_id=trace_id,
            )


DEFAULT_FOCAL_ORCHESTRATOR = FocalConversationOrchestrator()

