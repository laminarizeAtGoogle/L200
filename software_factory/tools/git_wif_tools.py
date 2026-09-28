"""Git feature-branch workflow, Cross-Project WIF onboarding, and PR delivery tools.

Enforces repository governance:
- Never commits or pushes directly to `main`.
- Always creates isolated feature branches from `main`.
- Formats commits with multi-line context (`Why:`, `What:`, `Verification:`).
- Onboards external workspaces and GCP projects via Workload Identity Federation (WIF).
- Opens Pull Requests targeting `main` to trigger WIF-authenticated `terraform apply`.
- Enforces Human-in-the-Loop confirmation for high-stakes actions.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from pydantic import ValidationError

from ..config import WORKSPACE_ROOT
from ..observability import (
    DEFAULT_INTENT_OUTCOME_RECORDER,
    DEFAULT_TELEMETRY,
)
from ..orchestration import (
    DEFAULT_GUARDRAILS_PLUGIN,
    DEFAULT_HITL_GATE,
)
from ..schemas import (
    CommitWorkspaceChangesInput,
    ConfigureCrossProjectWifInput,
    CreateFeatureBranchInput,
    GuidedToolResponse,
    HumanApprovalRequestInput,
    OpenPullRequestInput,
    ToolExecutionStatus,
)


def create_isolated_feature_branch_from_main(
    workspace_path: str,
    branch_name: str,
    base_branch: str = "main",
) -> dict[str, Any]:
    """Creates and checks out an isolated feature branch from `main`.

    Purpose:
        Enforces the mandatory policy that agents never push directly to `main`.
        Creates or switches to a dedicated feature branch (`feat/*`, `fix/*`,
        `refactor/*`, `docs/*`, `chore/*`, `factory/*`) in the target workspace.

    Args:
        workspace_path: Path to the target git repository.
        branch_name: Name of the feature branch (must start with a valid prefix
            such as `'feat/'` or `'factory/'` and must NEVER be `'main'`).
        base_branch: Base branch to branch from (defaults to `'main'`).

    Returns:
        A serialized `GuidedToolResponse` dictionary confirming the checked-out
        branch, or guided recovery steps if branch naming violates policy.
    """
    tool_name = "create_isolated_feature_branch_from_main"
    raw_args = {
        "workspace_path": workspace_path,
        "branch_name": branch_name,
        "base_branch": base_branch,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="wif_git_delivery_agent",
        intended_arguments=raw_args,
        rationale="Create isolated feature branch from main so main is never pushed directly",
    )

    with DEFAULT_TELEMETRY.start_span(tool_name, attributes=raw_args):
        violation = DEFAULT_GUARDRAILS_PLUGIN.evaluate_policy_on_tool_call(
            tool_name, raw_args
        )
        if violation is not None:
            res = violation.model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=res,
            )
            return res

        try:
            validated = CreateFeatureBranchInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid feature branch name or arguments.",
                error_code="INVALID_BRANCH_NAME",
                error_message=str(exc),
                remediation_steps=[
                    "Use a branch name matching `^(feat|fix|refactor|docs|chore|factory)/[a-zA-Z0-9._-]+$` (e.g., 'feat/a2a-software-factory' or 'factory/v1').",
                    "Never pass `branch_name='main'` or `branch_name='master'`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        repo_dir = Path(validated.workspace_path).expanduser().resolve()
        if not (repo_dir / ".git").exists():
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"'{repo_dir}' is not a git repository.",
                error_code="NOT_A_GIT_REPOSITORY",
                error_message=f"No .git directory found in '{repo_dir}'.",
                remediation_steps=[
                    "Verify `workspace_path` points to an initialized git repository.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        # Check if branch already exists
        check_res = subprocess.run(
            ["git", "rev-parse", "--verify", validated.branch_name],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if check_res.returncode == 0:
            co_res = subprocess.run(
                ["git", "checkout", validated.branch_name],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        else:
            co_res = subprocess.run(
                ["git", "checkout", "-b", validated.branch_name],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

        if co_res.returncode != 0:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Failed to checkout branch '{validated.branch_name}'.",
                error_code="GIT_CHECKOUT_FAILED",
                error_message=co_res.stderr.strip() or co_res.stdout.strip(),
                remediation_steps=[
                    "Inspect `git status` in the workspace for conflicting untracked files.",
                    "Resolve or stash conflicting changes before switching branches.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Checked out isolated feature branch '{validated.branch_name}' "
                f"(base='{validated.base_branch}') in '{repo_dir.name}'."
            ),
            data={
                "workspace_path": str(repo_dir),
                "active_branch": validated.branch_name,
                "base_branch": validated.base_branch,
                "protected_main_enforced": True,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def commit_workspace_changes_with_context(
    workspace_path: str,
    commit_type: str,
    scope: str,
    subject: str,
    why_bullets: list[str],
    what_bullets: list[str],
    verification_bullets: list[str],
    stage_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Stages and commits workspace changes using the mandatory multi-line format.

    Purpose:
        Enforces `AGENTS.md` Section 1.A (Multi-Line Commits with `Why:`,
        `What:`, and `Verification:` sections) and blocks committing directly on
        the protected `main` branch.

    Args:
        workspace_path: Path to the target git repository.
        commit_type: Conventional commit type (`feat`, `fix`, `refactor`, `docs`,
            `test`, `chore`, `ci`).
        scope: Component scope (e.g., `'a2a'`, `'terraform'`, `'wif'`).
        subject: Concise imperative subject line (5-72 chars).
        why_bullets: Non-empty list of motivation/problem statement bullets.
        what_bullets: Non-empty list of technical changes made.
        verification_bullets: Non-empty list of verification steps performed.
        stage_paths: Paths to stage with `git add` (defaults to `['.']`).

    Returns:
        A serialized `GuidedToolResponse` dictionary with the commit SHA and
        formatted message, or guided remediation steps if on `main`.
    """
    tool_name = "commit_workspace_changes_with_context"
    raw_args = {
        "workspace_path": workspace_path,
        "commit_type": commit_type,
        "scope": scope,
        "subject": subject,
        "why_bullets": why_bullets,
        "what_bullets": what_bullets,
        "verification_bullets": verification_bullets,
        "stage_paths": stage_paths or ["."],
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="wif_git_delivery_agent",
        intended_arguments=raw_args,
        rationale="Commit staged changes on feature branch with Why/What/Verification context",
    )

    with DEFAULT_TELEMETRY.start_span(
        tool_name,
        attributes={
            "workspace_path": workspace_path,
            "commit_type": commit_type,
            "scope": scope,
        },
    ):
        try:
            validated = CommitWorkspaceChangesInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Commit arguments failed schema validation.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Use a valid `commit_type` ('feat', 'fix', 'refactor', 'docs', 'test', 'chore', 'ci').",
                    "Provide at least one bullet in `why_bullets`, `what_bullets`, and `verification_bullets`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        repo_dir = Path(validated.workspace_path).expanduser().resolve()
        br_res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        current_branch = br_res.stdout.strip()
        if current_branch in {"main", "master"}:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                tool_name=tool_name,
                summary=f"Guardrail blocked direct commit on protected branch '{current_branch}'.",
                error_code="PROTECTED_BRANCH_COMMIT_BLOCKED",
                error_message=(
                    f"Active branch is '{current_branch}'. Direct commits to '{current_branch}' are forbidden."
                ),
                remediation_steps=[
                    "First call `create_isolated_feature_branch_from_main` to switch to a feature branch (e.g., 'feat/my-change').",
                    "Then retry `commit_workspace_changes_with_context`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=resp,
            )
            return resp

        header = f"{validated.commit_type}({validated.scope}): {validated.subject}"
        why_section = "Why:\n" + "\n".join(f"- {b}" for b in validated.why_bullets)
        what_section = "What:\n" + "\n".join(f"- {b}" for b in validated.what_bullets)
        ver_section = "Verification:\n" + "\n".join(
            f"- {b}" for b in validated.verification_bullets
        )
        extended_body = f"{why_section}\n\n{what_section}\n\n{ver_section}"

        subprocess.run(
            ["git", "add", *validated.stage_paths],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        commit_res = subprocess.run(
            ["git", "commit", "-m", header, "-m", extended_body],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if commit_res.returncode != 0:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Git commit failed (working tree may be clean or identity unset).",
                error_code="GIT_COMMIT_FAILED",
                error_message=commit_res.stderr.strip() or commit_res.stdout.strip(),
                remediation_steps=[
                    "Verify that files were modified before calling `commit_workspace_changes_with_context`.",
                    "Check `inspect_target_workspace_state` to see `working_tree_changes`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        sha_res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        commit_sha = sha_res.stdout.strip()

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=f"Created multi-line commit {commit_sha} on branch '{current_branch}': {header}",
            data={
                "workspace_path": str(repo_dir),
                "branch": current_branch,
                "commit_sha": commit_sha,
                "header": header,
                "body": extended_body,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def configure_cross_project_wif_federation(
    workspace_path: str,
    target_gcp_project_id: str,
    github_repo: str,
    workload_identity_pool: str = "github-actions-pool",
    workload_identity_provider: str = "github-provider",
    deployer_service_account_name: str = "github-terraform-deployer",
    tf_state_bucket: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Configures Workload Identity Federation (WIF) to onboard an external workspace/project.

    Purpose:
        Allows the Software Factory to be brought into any external workspace or
        target a different GCP project via keyless OIDC Workload Identity
        Federation. Generates the WIF onboarding manifest
        (`.factory_wif_manifest.json`) and provides the exact provisioning
        invocation for `scripts/setup-argolis-github-wif.sh`.

    Args:
        workspace_path: Target workspace filesystem path.
        target_gcp_project_id: Target GCP project ID (strictly lowercase).
        github_repo: GitHub repository in `'OWNER/REPO'` format.
        workload_identity_pool: Workload Identity Pool ID.
        workload_identity_provider: Workload Identity OIDC Provider ID.
        deployer_service_account_name: Deployer Service Account name.
        tf_state_bucket: Remote GCS bucket for Terraform state.
        dry_run: If True (default), writes the WIF configuration manifest without
            mutating live GCP IAM bindings directly from Cloudtop.

    Returns:
        A serialized `GuidedToolResponse` dictionary containing the WIF provider
        URI template, deployer SA email, state bucket, and GitHub Actions
        variables required for keyless `terraform apply`.
    """
    tool_name = "configure_cross_project_wif_federation"
    raw_args = {
        "workspace_path": workspace_path,
        "target_gcp_project_id": target_gcp_project_id,
        "github_repo": github_repo,
        "workload_identity_pool": workload_identity_pool,
        "workload_identity_provider": workload_identity_provider,
        "deployer_service_account_name": deployer_service_account_name,
        "tf_state_bucket": tf_state_bucket,
        "dry_run": dry_run,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="wif_git_delivery_agent",
        intended_arguments=raw_args,
        rationale=(
            f"Configure cross-project WIF federation for repo '{github_repo}' "
            f"targeting GCP project '{target_gcp_project_id}'"
        ),
    )

    with DEFAULT_TELEMETRY.start_span(tool_name, attributes=raw_args):
        try:
            validated = ConfigureCrossProjectWifInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid cross-project WIF configuration parameters.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Ensure `target_gcp_project_id` is lowercase (e.g., 'l200-509515').",
                    "Ensure `github_repo` is formatted as 'OWNER/REPO' (e.g., 'laminarizeAtGoogle/L200').",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        target_dir = Path(validated.workspace_path).expanduser().resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Target workspace '{target_dir}' not found.",
                error_code="WORKSPACE_NOT_FOUND",
                error_message=f"Directory '{target_dir}' does not exist.",
                remediation_steps=[
                    "Provide an existing workspace directory path.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        bucket_name = (
            validated.tf_state_bucket
            or f"{validated.target_gcp_project_id}-tfstate"
        )
        deployer_sa_email = (
            f"{validated.deployer_service_account_name}@"
            f"{validated.target_gcp_project_id}.iam.gserviceaccount.com"
        )
        readonly_sa_email = (
            f"cloudtop-agent-reader@"
            f"{validated.target_gcp_project_id}.iam.gserviceaccount.com"
        )
        wif_provider_template = (
            f"projects/<PROJECT_NUMBER>/locations/global/"
            f"workloadIdentityPools/{validated.workload_identity_pool}/"
            f"providers/{validated.workload_identity_provider}"
        )
        setup_script = WORKSPACE_ROOT / "scripts" / "setup-argolis-github-wif.sh"

        wif_manifest = {
            "target_workspace": str(target_dir),
            "target_gcp_project_id": validated.target_gcp_project_id,
            "github_repo": validated.github_repo,
            "authentication_mode": "keyless_oidc_workload_identity_federation",
            "workload_identity_pool": validated.workload_identity_pool,
            "workload_identity_provider": validated.workload_identity_provider,
            "wif_provider_resource_template": wif_provider_template,
            "deployer_service_account": deployer_sa_email,
            "readonly_probe_service_account": readonly_sa_email,
            "tf_state_bucket": bucket_name,
            "github_actions_variables": {
                "GCP_PROJECT_ID": validated.target_gcp_project_id,
                "GCP_WORKLOAD_IDENTITY_PROVIDER": wif_provider_template,
                "GCP_SERVICE_ACCOUNT": deployer_sa_email,
                "TF_STATE_BUCKET": bucket_name,
            },
            "bootstrap_command": (
                f"{setup_script} --project {validated.target_gcp_project_id} "
                f"--repo {validated.github_repo} "
                f"--sa-name {validated.deployer_service_account_name} "
                f"--bucket {bucket_name}"
            ),
            "dry_run": validated.dry_run,
        }

        manifest_file = target_dir / ".factory_state" / "wif_onboarding.json"
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(
            json.dumps(wif_manifest, indent=2), encoding="utf-8"
        )

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Configured cross-project WIF federation for '{validated.github_repo}' "
                f"-> GCP project '{validated.target_gcp_project_id}' "
                f"(Deployer SA: {deployer_sa_email})."
            ),
            data=wif_manifest,
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def open_pull_request_for_terraform_apply(
    workspace_path: str,
    title: str,
    summary: str,
    changes_included: list[str],
    review_decisions: list[str],
    test_coverage: list[str],
    base_branch: str = "main",
    head_branch: str | None = None,
    dry_run: bool = False,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Opens a GitHub Pull Request from a feature branch to `main` to trigger Terraform CI/CD.

    Purpose:
        Because direct pushes to `main` and local `terraform apply` runs are
        strictly prohibited, this tool prepares and opens a comprehensive Pull
        Request conforming to `AGENTS.md` Section 1.B (Summary, Changes Included,
        Review & Discussion Decisions, Test Coverage) so GitHub Actions executes
        `terraform-plan.yml` on the PR and `terraform-apply.yml` upon merge.

    Args:
        workspace_path: Path to the target git repository.
        title: Pull Request title (`<type>(<scope>): <subject>`).
        summary: High-level summary of intent.
        changes_included: Bulleted breakdown of technical and Terraform changes.
        review_decisions: Key architectural and security decisions.
        test_coverage: Verification and test results.
        base_branch: Target base branch (defaults to `'main'`).
        head_branch: Source feature branch (must NOT be `'main'`).
        dry_run: If True, validates branch policy and returns the formatted PR
            payload without invoking the remote GitHub API.
        approval_token: Optional Human-in-the-Loop approval token ID.

    Returns:
        A serialized `GuidedToolResponse` dictionary containing the formatted PR
        body, branch metadata, and PR URL (or dry-run verification).
    """
    tool_name = "open_pull_request_for_terraform_apply"
    raw_args = {
        "workspace_path": workspace_path,
        "title": title,
        "summary": summary,
        "changes_included": changes_included,
        "review_decisions": review_decisions,
        "test_coverage": test_coverage,
        "base_branch": base_branch,
        "head_branch": head_branch,
        "dry_run": dry_run,
        "approval_token": approval_token,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="wif_git_delivery_agent",
        intended_arguments=raw_args,
        rationale="Open Pull Request from feature branch to main to trigger WIF Terraform CI/CD",
    )

    with DEFAULT_TELEMETRY.start_span(
        tool_name,
        attributes={
            "workspace_path": workspace_path,
            "title": title,
            "base_branch": base_branch,
            "head_branch": head_branch or "auto",
            "dry_run": dry_run,
        },
    ):
        violation = DEFAULT_GUARDRAILS_PLUGIN.evaluate_policy_on_tool_call(
            tool_name, raw_args
        )
        if violation is not None:
            res = violation.model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=res,
            )
            return res

        try:
            validated = OpenPullRequestInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Pull Request arguments failed schema validation.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Provide a `title` between 10 and 120 characters.",
                    "Provide non-empty lists for `changes_included`, `review_decisions`, and `test_coverage`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        repo_dir = Path(validated.workspace_path).expanduser().resolve()
        resolved_head = validated.head_branch
        if not resolved_head:
            br_res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            resolved_head = br_res.stdout.strip()

        if not resolved_head or resolved_head in {"main", "master"}:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                tool_name=tool_name,
                summary="Cannot open a Pull Request from protected branch 'main'.",
                error_code="PROTECTED_HEAD_BRANCH",
                error_message=(
                    f"Source branch is '{resolved_head}'. Pull requests must originate from an isolated feature branch."
                ),
                remediation_steps=[
                    "Call `create_isolated_feature_branch_from_main` to create a feature branch.",
                    "Commit your changes on that branch and retry `open_pull_request_for_terraform_apply`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=resp,
            )
            return resp

        changes_md = "\n".join(f"- {item}" for item in validated.changes_included)
        decisions_md = "\n".join(f"- {item}" for item in validated.review_decisions)
        tests_md = "\n".join(f"- {item}" for item in validated.test_coverage)

        pr_body = (
            f"## Summary\n{validated.summary}\n\n"
            f"## Changes Included\n{changes_md}\n\n"
            f"## Review & Discussion Decisions\n{decisions_md}\n\n"
            f"## Test Coverage\n{tests_md}\n"
        )

        if validated.dry_run:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.SUCCESS,
                tool_name=tool_name,
                summary=(
                    f"Validated Pull Request '{validated.title}' "
                    f"({resolved_head} -> {validated.base_branch}) in dry-run mode."
                ),
                data={
                    "workspace_path": str(repo_dir),
                    "head_branch": resolved_head,
                    "base_branch": validated.base_branch,
                    "title": validated.title,
                    "pr_body": pr_body,
                    "dry_run": True,
                },
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="success",
                actual_result=resp,
            )
            return resp

        gh_bin = str(WORKSPACE_ROOT / "bin" / "gh")
        if not Path(gh_bin).is_file():
            gh_bin = shutil.which("gh") or "gh"

        pr_res = subprocess.run(
            [
                gh_bin,
                "pr",
                "create",
                "--base",
                validated.base_branch,
                "--head",
                resolved_head,
                "--title",
                validated.title,
                "--body",
                pr_body,
            ],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if pr_res.returncode != 0:
            err_out = pr_res.stderr.strip() or pr_res.stdout.strip()
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="GitHub CLI PR creation returned an error.",
                error_code="GH_PR_CREATE_FAILED",
                error_message=err_out,
                remediation_steps=[
                    f"Ensure branch '{resolved_head}' has been pushed to origin (`git push -u origin {resolved_head}`).",
                    "Ensure `./bin/gh auth status` is authenticated or pass `dry_run=True` when testing offline.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        pr_url = pr_res.stdout.strip()
        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=f"Opened Pull Request {pr_url} ({resolved_head} -> {validated.base_branch}).",
            data={
                "workspace_path": str(repo_dir),
                "head_branch": resolved_head,
                "base_branch": validated.base_branch,
                "title": validated.title,
                "pr_url": pr_url,
                "pr_body": pr_body,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def request_human_approval_for_high_stakes_action(
    action_type: str,
    target_workspace: str,
    target_project_id: str,
    proposed_command_or_diff: str,
    risk_assessment: str,
) -> dict[str, Any]:
    """Requests explicit Human-in-the-Loop (HITL) approval before high-stakes actions.

    Purpose:
        Implements a mandatory execution pause before merging a Pull Request to
        trigger `terraform apply`, altering cross-project WIF IAM bindings, or
        executing destructive changes. Creates an approval ticket that can be
        approved or rejected via `POST /api/v1/approvals/{approval_id}`.

    Args:
        action_type: One of `'merge_pull_request_terraform_apply'`,
            `'cross_project_wif_iam_binding'`, or `'destructive_resource_change'`.
        target_workspace: Workspace or GitHub repository affected.
        target_project_id: Target GCP project ID affected.
        proposed_command_or_diff: Exact PR URL, Terraform plan summary, or IAM
            binding command awaiting human sign-off.
        risk_assessment: Blast radius and rollback analysis.

    Returns:
        A serialized `GuidedToolResponse` with `status="pending_approval"` and
        the generated `approval_id`.
    """
    tool_name = "request_human_approval_for_high_stakes_action"
    raw_args = {
        "action_type": action_type,
        "target_workspace": target_workspace,
        "target_project_id": target_project_id,
        "proposed_command_or_diff": proposed_command_or_diff,
        "risk_assessment": risk_assessment,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="wif_git_delivery_agent",
        intended_arguments=raw_args,
        rationale="Pause execution and request Human-in-the-Loop confirmation for high-stakes action",
    )

    with DEFAULT_TELEMETRY.start_span(tool_name, attributes=raw_args):
        try:
            validated = HumanApprovalRequestInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid arguments for Human-in-the-Loop approval request.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Set `action_type` to 'merge_pull_request_terraform_apply', 'cross_project_wif_iam_binding', or 'destructive_resource_change'.",
                    "Provide non-empty `target_workspace`, `target_project_id`, `proposed_command_or_diff`, and `risk_assessment`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        ticket = DEFAULT_HITL_GATE.create_approval_request(
            action_type=validated.action_type,
            target_workspace=validated.target_workspace,
            target_project_id=validated.target_project_id,
            proposed_command_or_diff=validated.proposed_command_or_diff,
            risk_assessment=validated.risk_assessment,
        )

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.PENDING_APPROVAL,
            tool_name=tool_name,
            summary=(
                f"Execution paused awaiting Human-in-the-Loop approval "
                f"(approval_id='{ticket['approval_id']}') for '{validated.action_type}'."
            ),
            data=ticket,
            remediation_steps=[
                f"Present `approval_id='{ticket['approval_id']}'` and the `risk_assessment` to the user.",
                f"Wait for the human operator to approve via `POST /api/v1/approvals/{ticket['approval_id']}` before proceeding.",
            ],
            retryable=False,
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="pending_approval",
            actual_result=resp,
        )
        return resp
