"""Strict Pydantic v2 JSON schemas for tools, agents, and conversational API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolExecutionStatus(str, Enum):
    """Standardized execution status returned by all factory tools."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING_APPROVAL = "pending_approval"
    BLOCKED_BY_GUARDRAIL = "blocked_by_guardrail"


class GuidedToolResponse(BaseModel):
    """Strict output schema for all agent tools with guided LLM error recovery."""

    model_config = ConfigDict(extra="forbid")

    status: ToolExecutionStatus = Field(
        ...,
        description="Execution status of the tool call.",
    )
    tool_name: str = Field(
        ...,
        description="Canonical name of the invoked tool.",
    )
    summary: str = Field(
        ...,
        description="Concise human- and LLM-readable summary of the result.",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured payload returned by the tool on success.",
    )
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code when status is error or blocked.",
    )
    error_message: str | None = Field(
        default=None,
        description="Detailed error message explaining what failed.",
    )
    remediation_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Actionable recovery instructions guiding the LLM on how to fix "
            "the arguments, switch branches, or request approval instead of crashing."
        ),
    )
    retryable: bool = Field(
        default=False,
        description="Whether the LLM should retry the operation after applying remediation_steps.",
    )


class InspectWorkspaceInput(BaseModel):
    """Input schema for inspecting a target workspace directory."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Absolute or relative filesystem path to the target workspace.",
    )
    include_git_status: bool = Field(
        default=True,
        description="Whether to inspect active git branch, remote URL, and working tree status.",
    )
    max_files: int = Field(
        default=200,
        ge=1,
        le=1000,
        description="Maximum number of tracked files to return in the manifest.",
    )


class GenerateSoftwareArtifactInput(BaseModel):
    """Input schema for generating or updating software artifacts in a workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Target workspace root directory where the file will be written.",
    )
    relative_file_path: str = Field(
        ...,
        min_length=1,
        description="Relative file path inside the workspace (must not escape workspace root).",
    )
    content: str = Field(
        ...,
        description="Complete source code or configuration content to write.",
    )
    artifact_purpose: str = Field(
        ...,
        min_length=5,
        description="Clear explanation of what this file implements and why.",
    )
    overwrite: bool = Field(
        default=True,
        description="Whether to overwrite the file if it already exists.",
    )


class SynthesizeTerraformModuleInput(BaseModel):
    """Input schema for synthesizing Terraform IaC resources in a target workspace."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Target workspace path containing a terraform/ directory.",
    )
    target_gcp_project_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
        description="Lowercase GCP project ID where resources will be deployed via WIF.",
    )
    region: str = Field(
        default="us-central1",
        description="Default GCP region for Terraform resources.",
    )
    resource_HCL: str = Field(
        ...,
        min_length=10,
        description="Valid Terraform HCL resource blocks to write into the target module.",
    )
    module_filename: str = Field(
        default="factory_resources.tf",
        pattern=r"^[a-zA-Z0-9_-]+\.tf$",
        description="Terraform filename inside the workspace's terraform/ directory.",
    )
    run_terraform_validate: bool = Field(
        default=True,
        description="Whether to run 'terraform fmt' and 'terraform validate' after writing.",
    )


class CreateFeatureBranchInput(BaseModel):
    """Input schema for creating an isolated feature branch from main."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Filesystem path of the target git repository.",
    )
    branch_name: str = Field(
        ...,
        pattern=r"^(feat|fix|refactor|docs|chore|factory)/[a-zA-Z0-9._-]+$",
        description="Feature branch name (e.g., 'feat/add-cloud-run-service'). Never 'main' or 'master'.",
    )
    base_branch: str = Field(
        default="main",
        description="Base branch to branch off from (defaults to 'main').",
    )


class CommitWorkspaceChangesInput(BaseModel):
    """Input schema for creating a multi-line context-preserving git commit."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Filesystem path of the target git repository.",
    )
    commit_type: Literal["feat", "fix", "refactor", "docs", "test", "chore", "ci"] = Field(
        ...,
        description="Conventional commit type.",
    )
    scope: str = Field(
        ...,
        min_length=2,
        max_length=40,
        description="Component scope of the commit (e.g., 'a2a', 'terraform', 'wif').",
    )
    subject: str = Field(
        ...,
        min_length=5,
        max_length=72,
        description="Concise imperative subject line.",
    )
    why_bullets: list[str] = Field(
        ...,
        min_length=1,
        description="Motivation, problem statement, or requirement bullets.",
    )
    what_bullets: list[str] = Field(
        ...,
        min_length=1,
        description="Specific files, components, and technical changes included.",
    )
    verification_bullets: list[str] = Field(
        ...,
        min_length=1,
        description="How the change was tested and validated.",
    )
    stage_paths: list[str] = Field(
        default_factory=lambda: ["."],
        description="Paths to stage prior to committing.",
    )


class ConfigureCrossProjectWifInput(BaseModel):
    """Input schema for onboarding an external workspace/project with WIF."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Target workspace path where WIF workflows and backend configs live.",
    )
    target_gcp_project_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
        description="Target GCP project ID to connect via Workload Identity Federation.",
    )
    github_repo: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
        description="GitHub repository in 'OWNER/REPO' format authorized for OIDC federation.",
    )
    workload_identity_pool: str = Field(
        default="github-actions-pool",
        description="Workload Identity Pool identifier.",
    )
    workload_identity_provider: str = Field(
        default="github-provider",
        description="Workload Identity OIDC Provider identifier.",
    )
    deployer_service_account_name: str = Field(
        default="github-terraform-deployer",
        description="Service Account name assumed by GitHub Actions during terraform apply.",
    )
    tf_state_bucket: str | None = Field(
        default=None,
        description="Remote GCS bucket for Terraform state (defaults to '<project_id>-tfstate').",
    )
    dry_run: bool = Field(
        default=True,
        description="If true, generates the WIF onboarding manifest and workflow files without mutating live IAM.",
    )


class OpenPullRequestInput(BaseModel):
    """Input schema for opening a pull request from a feature branch to main."""

    model_config = ConfigDict(extra="forbid")

    workspace_path: str = Field(
        ...,
        min_length=1,
        description="Filesystem path of the target git repository.",
    )
    title: str = Field(
        ...,
        min_length=10,
        max_length=120,
        description="Pull Request title (embedded into merge commit title on main).",
    )
    summary: str = Field(
        ...,
        min_length=10,
        description="High-level intent of the Pull Request.",
    )
    changes_included: list[str] = Field(
        ...,
        min_length=1,
        description="Itemized technical breakdown of changes.",
    )
    review_decisions: list[str] = Field(
        ...,
        min_length=1,
        description="Key architectural or security decisions.",
    )
    test_coverage: list[str] = Field(
        ...,
        min_length=1,
        description="Explicit test and verification results.",
    )
    base_branch: str = Field(
        default="main",
        description="Target base branch for the PR (always 'main' for Terraform apply).",
    )
    head_branch: str | None = Field(
        default=None,
        description="Source feature branch (cannot be 'main'). Defaults to active branch.",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, validates branch policy and renders the PR body without calling GitHub API.",
    )
    approval_token: str | None = Field(
        default=None,
        description="Human-in-the-loop approval token if required by policy.",
    )


class GcloudReadonlyProbeInput(BaseModel):
    """Input schema for probing live GCP resources using the read-only service account."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
        description="Target GCP project ID to inspect.",
    )
    resource_domain: Literal[
        "compute_instances",
        "storage_buckets",
        "service_accounts",
        "workload_identity_pools",
        "cloud_run_services",
        "secrets",
        "vpc_networks",
        "cloud_assets",
    ] = Field(
        ...,
        description="Read-only GCP resource category to probe.",
    )
    impersonate_service_account: str | None = Field(
        default=None,
        description="Read-only SA to impersonate (defaults to cloudtop-agent-reader@<project>.iam.gserviceaccount.com).",
    )
    filter_expression: str | None = Field(
        default=None,
        description="Optional gcloud --filter expression.",
    )


class QueryCloudLoggingInput(BaseModel):
    """Input schema for reading Cloud Logging entries in read-only mode."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$",
        description="Target GCP project ID whose logs will be queried.",
    )
    log_filter: str = Field(
        default='severity>="DEFAULT"',
        description="Cloud Logging filter expression.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of log entries to retrieve.",
    )
    impersonate_service_account: str | None = Field(
        default=None,
        description="Read-only SA to impersonate.",
    )


class HumanApprovalRequestInput(BaseModel):
    """Input schema for requesting Human-in-the-Loop confirmation before high-stakes actions."""

    model_config = ConfigDict(extra="forbid")

    action_type: Literal[
        "merge_pull_request_terraform_apply",
        "cross_project_wif_iam_binding",
        "destructive_resource_change",
    ] = Field(
        ...,
        description="Category of high-stakes action requiring human approval.",
    )
    target_workspace: str = Field(
        ...,
        description="Workspace or repository affected by the action.",
    )
    target_project_id: str = Field(
        ...,
        description="GCP project affected by the action.",
    )
    proposed_command_or_diff: str = Field(
        ...,
        description="Exact command, PR URL, or Terraform plan summary awaiting human confirmation.",
    )
    risk_assessment: str = Field(
        ...,
        description="Assessment of blast radius and rollback strategy.",
    )


class ChatMessageRequest(BaseModel):
    """Request schema for the single conversational focal point API (/api/v1/chat)."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        description="User intent or conversational message sent to the Focal Coordinator Agent.",
    )
    session_id: str = Field(
        default="default-session",
        min_length=1,
        description="Persistent session identifier.",
    )
    user_id: str = Field(
        default="engineer",
        min_length=1,
        description="Authenticated user identifier.",
    )
    workspace_path: str | None = Field(
        default=None,
        description="Optional path to the workspace the user wants software built in.",
    )
    target_gcp_project_id: str | None = Field(
        default=None,
        description="Optional external GCP project ID targeted via WIF.",
    )
    target_github_repo: str | None = Field(
        default=None,
        description="Optional GitHub repository ('OWNER/REPO') for PR-based Terraform delivery.",
    )


class AgentStateSummary(BaseModel):
    """State snapshot communicated from the A2A agent graph back to the user."""

    model_config = ConfigDict(extra="forbid")

    active_agent: str
    routed_model: str
    active_workspace: str
    active_branch: str | None = None
    target_gcp_project: str
    pending_approvals: list[dict[str, Any]] = Field(default_factory=list)
    invoked_subagents: list[str] = Field(default_factory=list)
    tool_executions: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None


class ChatMessageResponse(BaseModel):
    """Response schema from the single conversational focal point API."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    reply: str
    state: AgentStateSummary
    a2a_endpoints: dict[str, str]
