"""Unified FastAPI + A2A Server for the Agent Graph Software Factory.

Exposes:
1. The Single Conversational Focal Point API (`POST /api/v1/chat`) communicating
   state from specialist agents to the user and intent from the user to the
   agent graph.
2. Direct Software Factory endpoints for cross-workspace builds
   (`POST /api/v1/workspaces/build`), cross-project WIF onboarding
   (`POST /api/v1/workspaces/onboard`), read-only `gcloud` probing
   (`POST /api/v1/probe`), Human-in-the-Loop approvals
   (`POST /api/v1/approvals/{approval_id}`), and observability/tracing
   inspection (`GET /api/v1/observability/*`).
3. Native A2A Protocol endpoints (`/.well-known/agent.json` and JSON-RPC)
   mounted under `/a2a/focal`, `/a2a/architect`, `/a2a/builder`,
   `/a2a/wif_delivery`, and `/a2a/gcloud_probe`.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..agents import (
    A2A_AGENT_ROUTES,
    DEFAULT_FOCAL_ORCHESTRATOR,
    build_all_agent_cards,
    create_a2a_subapps,
)
from ..config import DEFAULT_CONFIG, FactoryConfig
from ..memory import (
    DEFAULT_ASYNC_CONSOLIDATOR,
    DEFAULT_MEMORY_STORE,
)
from ..observability import (
    DEFAULT_INTENT_OUTCOME_RECORDER,
    DEFAULT_LOGGER,
    DEFAULT_TELEMETRY,
)
from ..orchestration import DEFAULT_HITL_GATE
from ..schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConfigureCrossProjectWifInput,
    GcloudReadonlyProbeInput,
)
from ..tools import (
    commit_workspace_changes_with_context,
    configure_cross_project_wif_federation,
    create_isolated_feature_branch_from_main,
    generate_workspace_software_artifact,
    open_pull_request_for_terraform_apply,
    probe_gcp_resources_readonly,
    synthesize_cross_project_terraform_module,
)


class WorkspaceBuildRequest(BaseModel):
    """Request schema to build software and/or Terraform in a target workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        description="Target workspace path (can be this workspace or an external workspace).",
    )
    feature_branch: str = Field(
        ...,
        pattern=r"^(feat|fix|refactor|docs|chore|factory)/[a-zA-Z0-9._-]+$",
        description="Isolated feature branch to create/checkout from main.",
    )
    artifacts: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {'relative_file_path', 'content', 'artifact_purpose'} dicts to generate.",
    )
    terraform_module: dict[str, Any] | None = Field(
        default=None,
        description="Optional {'target_gcp_project_id', 'resource_HCL', 'module_filename'} dict.",
    )
    commit_info: dict[str, Any] | None = Field(
        default=None,
        description="Optional multi-line commit metadata.",
    )
    pull_request_info: dict[str, Any] | None = Field(
        default=None,
        description="Optional Pull Request metadata (runs in dry_run mode by default unless specified).",
    )


class ApprovalResolutionRequest(BaseModel):
    """Request schema for approving or rejecting a Human-in-the-Loop ticket."""

    model_config = ConfigDict(extra="forbid")

    approved: bool = Field(
        ...,
        description="True to approve execution, False to reject.",
    )
    reviewer: str = Field(
        default="human-operator",
        description="Identity of the human reviewer.",
    )
    comment: str = Field(
        default="",
        description="Optional review rationale.",
    )


def create_software_factory_api(
    config: FactoryConfig = DEFAULT_CONFIG,
) -> FastAPI:
    """Creates the unified FastAPI + A2A application."""
    a2a_subapps = create_a2a_subapps(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            for subapp in a2a_subapps.values():
                await stack.enter_async_context(
                    subapp.router.lifespan_context(subapp)
                )
            DEFAULT_LOGGER.log_event(
                event_type="SOFTWARE_FACTORY_API_STARTED",
                message="A2A Software Factory API and mounted A2A sub-apps initialized",
                metadata={"routes": list(a2a_subapps.keys())},
            )
            yield
            await DEFAULT_ASYNC_CONSOLIDATOR.flush_pending_tasks()

    app = FastAPI(
        title="A2A Agent Graph Software Factory API",
        version="1.0.0",
        description=(
            "Single conversational focal point and A2A multi-agent software "
            "factory with cross-project WIF onboarding, isolated feature-branch "
            "PR delivery, and read-only gcloud verification."
        ),
        lifespan=lifespan,
    )

    for mount_path, subapp in a2a_subapps.items():
        app.mount(mount_path, subapp)

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "app_name": config.app_name,
            "default_gcp_project": config.project_id,
            "readonly_service_account": config.readonly_service_account,
            "deployer_service_account": config.deployer_service_account,
            "models": {
                "planning": config.planning_model,
                "fast_execution": config.fast_model,
            },
            "a2a_routes": A2A_AGENT_ROUTES,
        }

    @app.post("/api/v1/chat", response_model=ChatMessageResponse)
    async def chat_with_focal_agent(
        request: ChatMessageRequest,
    ) -> ChatMessageResponse:
        """Single conversational focal point communicating intent and agent state."""
        return await DEFAULT_FOCAL_ORCHESTRATOR.handle_chat(
            request=request,
            a2a_endpoints=A2A_AGENT_ROUTES,
        )

    @app.post("/api/v1/workspaces/build")
    async def build_in_workspace(
        request: WorkspaceBuildRequest,
    ) -> dict[str, Any]:
        """Executes a multi-step software & Terraform build on a feature branch."""
        with DEFAULT_TELEMETRY.start_span(
            "api.build_in_workspace",
            attributes={
                "workspace_path": request.workspace_path,
                "feature_branch": request.feature_branch,
            },
        ):
            steps: list[dict[str, Any]] = []

            # 1. Create or checkout isolated feature branch from main
            branch_res = create_isolated_feature_branch_from_main(
                workspace_path=request.workspace_path,
                branch_name=request.feature_branch,
            )
            steps.append(branch_res)
            if branch_res.get("status") != "success":
                return {"status": "failed", "steps": steps}

            # 2. Generate requested software artifacts
            for artifact in request.artifacts:
                art_res = generate_workspace_software_artifact(
                    workspace_path=request.workspace_path,
                    relative_file_path=artifact["relative_file_path"],
                    content=artifact["content"],
                    artifact_purpose=artifact.get(
                        "artifact_purpose", "Generated by A2A Software Factory"
                    ),
                )
                steps.append(art_res)

            # 3. Synthesize optional cross-project Terraform module
            if request.terraform_module:
                tf_res = synthesize_cross_project_terraform_module(
                    workspace_path=request.workspace_path,
                    target_gcp_project_id=request.terraform_module[
                        "target_gcp_project_id"
                    ],
                    resource_HCL=request.terraform_module["resource_HCL"],
                    module_filename=request.terraform_module.get(
                        "module_filename", "factory_resources.tf"
                    ),
                    run_terraform_validate=request.terraform_module.get(
                        "run_terraform_validate", True
                    ),
                )
                steps.append(tf_res)

            # 4. Optional multi-line git commit
            if request.commit_info:
                commit_res = commit_workspace_changes_with_context(
                    workspace_path=request.workspace_path,
                    commit_type=request.commit_info.get("commit_type", "feat"),
                    scope=request.commit_info.get("scope", "factory"),
                    subject=request.commit_info["subject"],
                    why_bullets=request.commit_info["why_bullets"],
                    what_bullets=request.commit_info["what_bullets"],
                    verification_bullets=request.commit_info[
                        "verification_bullets"
                    ],
                )
                steps.append(commit_res)

            # 5. Optional Pull Request preparation
            if request.pull_request_info:
                pr_res = open_pull_request_for_terraform_apply(
                    workspace_path=request.workspace_path,
                    title=request.pull_request_info["title"],
                    summary=request.pull_request_info["summary"],
                    changes_included=request.pull_request_info[
                        "changes_included"
                    ],
                    review_decisions=request.pull_request_info[
                        "review_decisions"
                    ],
                    test_coverage=request.pull_request_info["test_coverage"],
                    head_branch=request.feature_branch,
                    dry_run=request.pull_request_info.get("dry_run", True),
                )
                steps.append(pr_res)

            return {
                "status": "completed",
                "workspace_path": request.workspace_path,
                "feature_branch": request.feature_branch,
                "steps": steps,
            }

    @app.post("/api/v1/workspaces/onboard")
    async def onboard_external_workspace_wif(
        request: ConfigureCrossProjectWifInput,
    ) -> dict[str, Any]:
        """Onboards an external workspace and GCP project via Workload Identity Federation."""
        return configure_cross_project_wif_federation(
            workspace_path=request.workspace_path,
            target_gcp_project_id=request.target_gcp_project_id,
            github_repo=request.github_repo,
            workload_identity_pool=request.workload_identity_pool,
            workload_identity_provider=request.workload_identity_provider,
            deployer_service_account_name=request.deployer_service_account_name,
            tf_state_bucket=request.tf_state_bucket,
            dry_run=request.dry_run,
        )

    @app.post("/api/v1/probe")
    async def probe_gcp_readonly(
        request: GcloudReadonlyProbeInput,
    ) -> dict[str, Any]:
        """Executes a read-only gcloud resource probe using `cloudtop-agent-reader`."""
        return probe_gcp_resources_readonly(
            project_id=request.project_id,
            resource_domain=request.resource_domain,
            impersonate_service_account=request.impersonate_service_account,
            filter_expression=request.filter_expression,
        )

    @app.get("/api/v1/sessions/{session_id}/state")
    async def get_session_state(session_id: str) -> dict[str, Any]:
        """Returns persistent session workspace state and relevant episodic memories."""
        state = DEFAULT_MEMORY_STORE.get_session_workspace_state(session_id)
        memories = DEFAULT_MEMORY_STORE.search_memories(
            query=session_id,
            session_id=session_id,
            top_k=10,
        )
        return {
            "session_id": session_id,
            "workspace_state": state,
            "episodic_memories": memories,
            "pending_approvals": DEFAULT_HITL_GATE.list_pending_approvals(
                session_id
            ),
        }

    @app.get("/api/v1/approvals")
    async def list_pending_approvals(
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Lists pending Human-in-the-Loop confirmation tickets."""
        return {
            "pending_approvals": DEFAULT_HITL_GATE.list_pending_approvals(
                session_id
            )
        }

    @app.post("/api/v1/approvals/{approval_id}")
    async def resolve_approval_ticket(
        approval_id: str,
        resolution: ApprovalResolutionRequest,
    ) -> dict[str, Any]:
        """Approves or rejects a pending Human-in-the-Loop action ticket."""
        try:
            ticket = DEFAULT_HITL_GATE.resolve_approval(
                approval_id,
                approved=resolution.approved,
                reviewer=resolution.reviewer,
                comment=resolution.comment,
            )
            return {"status": "resolved", "ticket": ticket}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/agents/cards")
    async def list_a2a_agent_cards() -> dict[str, Any]:
        """Returns A2A AgentCard specifications for all agents in the Software Factory."""
        base_url = f"http://localhost:{config.port}"
        cards = await build_all_agent_cards(base_url=base_url)
        return {
            "a2a_routes": A2A_AGENT_ROUTES,
            "agent_cards": cards,
        }

    @app.get("/api/v1/observability/audit")
    async def get_intent_outcome_audit_trail() -> dict[str, Any]:
        """Returns paired Intent (before execution) and Outcome (after execution) records."""
        return {
            "audit_count": len(DEFAULT_INTENT_OUTCOME_RECORDER.audit_trail),
            "audit_trail": DEFAULT_INTENT_OUTCOME_RECORDER.audit_trail[-100:],
        }

    @app.get("/api/v1/observability/spans")
    async def get_distributed_trace_spans() -> dict[str, Any]:
        """Returns OpenTelemetry distributed tracing spans."""
        spans = DEFAULT_TELEMETRY.get_exported_spans()
        return {
            "span_count": len(spans),
            "spans": spans[-100:],
        }

    return app
