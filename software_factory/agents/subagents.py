"""Specialist ADK Sub-Agents and Multi-Agent Workflow Patterns (Sequential & Parallel).

Defines factory functions for:
1. `workspace_architect_agent` (Gemini 2.5 Pro): Inspects target workspaces and
   designs software, OpenSpec artifacts, and Mermaid/OKF architectures.
2. `software_builder_agent` (Gemini 2.5 Pro): Writes application code, unit
   tests, and cross-project Terraform HCL manifests.
3. `wif_git_delivery_agent` (Gemini 2.5 Pro): Creates feature branches from
   `main`, configures cross-project WIF, commits with context, and opens PRs.
4. `gcloud_readonly_probe_agent` (Gemini 2.5 Flash): Probes GCP resources,
   queries Cloud Logging, and verifies deployments using `cloudtop-agent-reader`.
5. `parallel_verification_agent` (`ParallelAgent`): Concurrently executes GCP
   resource inspection and Cloud Logging audit.
6. `software_delivery_pipeline` (`SequentialAgent`): End-to-end sequential
   software factory pipeline.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from ..orchestration import DEFAULT_MODEL_ROUTER
from ..prompts import (
    GCLOUD_READONLY_PROBE_CONSTITUTION,
    SOFTWARE_BUILDER_CONSTITUTION,
    WIF_GIT_DELIVERY_CONSTITUTION,
    WORKSPACE_ARCHITECT_CONSTITUTION,
)
from ..tools import (
    commit_workspace_changes_with_context,
    configure_cross_project_wif_federation,
    create_isolated_feature_branch_from_main,
    generate_workspace_software_artifact,
    inspect_target_workspace_state,
    open_pull_request_for_terraform_apply,
    probe_gcp_resources_readonly,
    query_cloud_logging_entries_readonly,
    request_human_approval_for_high_stakes_action,
    synthesize_cross_project_terraform_module,
    verify_deployed_argolis_infrastructure,
)


def build_workspace_architect_agent(
    name: str = "workspace_architect_agent",
) -> LlmAgent:
    """Builds the Workspace Architect & Spec Specialist Agent (routed to Gemini Pro)."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(name)
    return LlmAgent(
        name=name,
        model=routing.selected_model,
        description=(
            "Inspects local or external target workspaces, analyzes git and "
            "Terraform state, and designs modular software and Mermaid/OKF architectures."
        ),
        instruction=WORKSPACE_ARCHITECT_CONSTITUTION,
        tools=[inspect_target_workspace_state],
    )


def build_software_builder_agent(
    name: str = "software_builder_agent",
) -> LlmAgent:
    """Builds the Software & Cross-Project Terraform Builder Agent (routed to Gemini Pro)."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(name)
    return LlmAgent(
        name=name,
        model=routing.selected_model,
        description=(
            "Generates production application code, unit tests, and validated "
            "Terraform HCL modules inside the target workspace."
        ),
        instruction=SOFTWARE_BUILDER_CONSTITUTION,
        tools=[
            inspect_target_workspace_state,
            generate_workspace_software_artifact,
            synthesize_cross_project_terraform_module,
        ],
    )


def build_wif_git_delivery_agent(
    name: str = "wif_git_delivery_agent",
) -> LlmAgent:
    """Builds the WIF Onboarding, Git Branch & PR Delivery Agent (routed to Gemini Pro)."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(name)
    return LlmAgent(
        name=name,
        model=routing.selected_model,
        description=(
            "Creates isolated feature branches from main, configures cross-project "
            "Workload Identity Federation (WIF), creates multi-line context commits, "
            "requests Human-in-the-Loop approval, and opens Pull Requests to trigger "
            "Terraform apply in Argolis."
        ),
        instruction=WIF_GIT_DELIVERY_CONSTITUTION,
        tools=[
            create_isolated_feature_branch_from_main,
            commit_workspace_changes_with_context,
            configure_cross_project_wif_federation,
            open_pull_request_for_terraform_apply,
            request_human_approval_for_high_stakes_action,
        ],
    )


def build_gcloud_readonly_probe_agent(
    name: str = "gcloud_readonly_probe_agent",
) -> LlmAgent:
    """Builds the Read-Only gcloud Probe & Verification Agent (routed to Gemini Flash)."""
    routing = DEFAULT_MODEL_ROUTER.select_model_for_agent(name)
    return LlmAgent(
        name=name,
        model=routing.selected_model,
        description=(
            "Strictly read-only GCP inspector impersonating cloudtop-agent-reader "
            "to probe live GCP resources, read Cloud Logging, and verify deployed "
            "Argolis infrastructure."
        ),
        instruction=GCLOUD_READONLY_PROBE_CONSTITUTION,
        tools=[
            probe_gcp_resources_readonly,
            query_cloud_logging_entries_readonly,
            verify_deployed_argolis_infrastructure,
        ],
    )


def build_parallel_verification_agent(
    name: str = "parallel_verification_agent",
) -> ParallelAgent:
    """Builds an ADK ParallelAgent that concurrently probes GCP resources and reads Cloud Logs."""
    fast_model = DEFAULT_MODEL_ROUTER.select_model_for_agent(
        "fast_probe_worker"
    ).selected_model

    resource_inspector = LlmAgent(
        name="gcp_resource_inspector_agent",
        model=fast_model,
        description="Concurrently probes live GCP resources and verifies Terraform outputs.",
        instruction=GCLOUD_READONLY_PROBE_CONSTITUTION,
        tools=[
            probe_gcp_resources_readonly,
            verify_deployed_argolis_infrastructure,
        ],
    )
    log_auditor = LlmAgent(
        name="cloud_log_auditor_agent",
        model=fast_model,
        description="Concurrently queries Cloud Logging for errors and audit events.",
        instruction=GCLOUD_READONLY_PROBE_CONSTITUTION,
        tools=[query_cloud_logging_entries_readonly],
    )
    return ParallelAgent(
        name=name,
        description=(
            "Executes read-only GCP resource probing and Cloud Logging audit "
            "in parallel to verify infrastructure deployments rapidly."
        ),
        sub_agents=[resource_inspector, log_auditor],
    )


def build_software_delivery_sequential_pipeline(
    name: str = "software_delivery_pipeline",
) -> SequentialAgent:
    """Builds an ADK SequentialAgent executing the 4-stage Software Factory lifecycle."""
    return SequentialAgent(
        name=name,
        description=(
            "End-to-end Sequential Software Factory pipeline: "
            "1) Inspect & Architect -> 2) Build Software & Terraform -> "
            "3) Branch, WIF & Open PR -> 4) Verify via Read-Only gcloud Probe."
        ),
        sub_agents=[
            build_workspace_architect_agent(name="seq_workspace_architect"),
            build_software_builder_agent(name="seq_software_builder"),
            build_wif_git_delivery_agent(name="seq_wif_git_delivery"),
            build_gcloud_readonly_probe_agent(name="seq_gcloud_verifier"),
        ],
    )
