"""Workspace inspection, software artifact generation, and Terraform synthesis tools.

Provides strictly typed, schema-validated ADK tools that allow the Software
Factory agent graph to inspect local or external workspaces, generate software
and test files, and synthesize cross-project Terraform HCL configurations.
"""

from __future__ import annotations

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
from ..orchestration import DEFAULT_GUARDRAILS_PLUGIN
from ..schemas import (
    GenerateSoftwareArtifactInput,
    GuidedToolResponse,
    InspectWorkspaceInput,
    SynthesizeTerraformModuleInput,
    ToolExecutionStatus,
)


def _find_terraform_binary(workspace_dir: Path) -> str | None:
    """Locates the hermetic ./bin/terraform binary or system terraform."""
    candidates = [
        workspace_dir / "bin" / "terraform",
        WORKSPACE_ROOT / "bin" / "terraform",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which("terraform")


def inspect_target_workspace_state(
    workspace_path: str,
    include_git_status: bool = True,
    max_files: int = 200,
) -> dict[str, Any]:
    """Inspects a target workspace's directory structure, git branch, and Terraform setup.

    Purpose:
        Enables the Workspace Architect Agent (`workspace_architect_agent`) to
        survey any local or external workspace directory before planning software
        changes or cross-project infrastructure deployments.

    Args:
        workspace_path: Absolute or relative path to the target workspace root.
        include_git_status: If True, queries active git branch, remote URL, and
            working tree cleanliness.
        max_files: Maximum number of files to return in the workspace inventory
            (1 to 1000).

    Returns:
        A serialized `GuidedToolResponse` dictionary containing `workspace_path`,
        `active_branch`, `git_remote`, `is_git_repo`, `has_terraform_dir`,
        `has_openspec_dir`, and `files`, or guided recovery steps on failure.
    """
    tool_name = "inspect_target_workspace_state"
    raw_args = {
        "workspace_path": workspace_path,
        "include_git_status": include_git_status,
        "max_files": max_files,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="workspace_architect_agent",
        intended_arguments=raw_args,
        rationale="Inspect target workspace topology, git branch, and IaC state",
    )

    with DEFAULT_TELEMETRY.start_span(tool_name, attributes=raw_args):
        try:
            validated = InspectWorkspaceInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid input arguments for workspace inspection.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Provide a non-empty `workspace_path` string.",
                    "Ensure `max_files` is an integer between 1 and 1000.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
                error_details=str(exc),
            )
            return resp

        target_dir = Path(validated.workspace_path).expanduser().resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Target workspace directory '{target_dir}' does not exist.",
                error_code="WORKSPACE_NOT_FOUND",
                error_message=f"Directory not found at '{target_dir}'.",
                remediation_steps=[
                    f"Verify the path '{validated.workspace_path}' exists on disk.",
                    f"Use '{WORKSPACE_ROOT}' to target the primary L200 workspace, or initialize the external workspace directory first.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        active_branch: str | None = None
        git_remote: str | None = None
        git_status_short: list[str] = []
        is_git_repo = (target_dir / ".git").exists()

        if validated.include_git_status and is_git_repo:
            try:
                br_res = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=str(target_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if br_res.returncode == 0:
                    active_branch = br_res.stdout.strip() or "HEAD"

                rem_res = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=str(target_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if rem_res.returncode == 0:
                    git_remote = rem_res.stdout.strip()

                st_res = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=str(target_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if st_res.returncode == 0 and st_res.stdout.strip():
                    git_status_short = st_res.stdout.strip().splitlines()[:50]
            except Exception:
                pass

        # Collect workspace file inventory
        files: list[str] = []
        if is_git_repo:
            try:
                ls_res = subprocess.run(
                    ["git", "ls-files"],
                    cwd=str(target_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if ls_res.returncode == 0:
                    files = [
                        line.strip()
                        for line in ls_res.stdout.splitlines()
                        if line.strip()
                    ][: validated.max_files]
            except Exception:
                pass

        if not files:
            ignored_dirs = {".git", ".venv", ".python", ".nodejs", "__pycache__"}
            for item in sorted(target_dir.rglob("*")):
                if any(part in ignored_dirs for part in item.parts):
                    continue
                if item.is_file():
                    files.append(str(item.relative_to(target_dir)))
                    if len(files) >= validated.max_files:
                        break

        payload = {
            "workspace_path": str(target_dir),
            "is_git_repo": is_git_repo,
            "active_branch": active_branch,
            "git_remote": git_remote,
            "working_tree_changes": git_status_short,
            "has_terraform_dir": (target_dir / "terraform").is_dir(),
            "has_openspec_dir": (target_dir / "openspec").is_dir(),
            "has_docs_dir": (target_dir / "docs").is_dir(),
            "file_count": len(files),
            "files": files,
        }

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Inspected workspace '{target_dir.name}' "
                f"(branch='{active_branch}', {len(files)} files indexed)."
            ),
            data=payload,
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def generate_workspace_software_artifact(
    workspace_path: str,
    relative_file_path: str,
    content: str,
    artifact_purpose: str,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Generates or updates a source code, test, or specification file in a workspace.

    Purpose:
        Allows the Software Builder Agent (`software_builder_agent`) to build
        application modules, unit tests, OpenSpec proposals, or OKF documentation
        inside the user's active workspace or an external workspace.

    Args:
        workspace_path: Root directory of the target workspace.
        relative_file_path: Relative path within `workspace_path` (e.g.,
            `'src/service.py'` or `'tests/test_service.py'`). Cannot traverse
            outside `workspace_path`.
        content: Complete file content to write.
        artifact_purpose: Human-readable explanation of what this artifact
            accomplishes.
        overwrite: Whether to overwrite an existing file at `relative_file_path`.

    Returns:
        A serialized `GuidedToolResponse` dictionary containing the written path,
        byte size, and line count, or guided error remediation steps.
    """
    tool_name = "generate_workspace_software_artifact"
    raw_args = {
        "workspace_path": workspace_path,
        "relative_file_path": relative_file_path,
        "content": content,
        "artifact_purpose": artifact_purpose,
        "overwrite": overwrite,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="software_builder_agent",
        intended_arguments={
            **raw_args,
            "content": f"<{len(content)} bytes>",
        },
        rationale=artifact_purpose,
    )

    with DEFAULT_TELEMETRY.start_span(
        tool_name,
        attributes={
            "workspace_path": workspace_path,
            "relative_file_path": relative_file_path,
            "artifact_purpose": artifact_purpose,
        },
    ):
        guardrail_violation = (
            DEFAULT_GUARDRAILS_PLUGIN.evaluate_policy_on_tool_call(
                tool_name, raw_args
            )
        )
        if guardrail_violation is not None:
            result = guardrail_violation.model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=result,
            )
            return result

        try:
            validated = GenerateSoftwareArtifactInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid arguments for software artifact generation.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Ensure `workspace_path` and `relative_file_path` are non-empty strings.",
                    "Provide an `artifact_purpose` of at least 5 characters.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        root_dir = Path(validated.workspace_path).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Workspace directory '{root_dir}' does not exist.",
                error_code="WORKSPACE_NOT_FOUND",
                error_message=f"Cannot write artifact because '{root_dir}' was not found.",
                remediation_steps=[
                    "Call `inspect_target_workspace_state` to confirm the correct workspace path.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        target_file = (root_dir / validated.relative_file_path).resolve()
        if not str(target_file).startswith(str(root_dir)):
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.BLOCKED_BY_GUARDRAIL,
                tool_name=tool_name,
                summary="Blocked file write escaping workspace root.",
                error_code="PATH_ESCAPE_BLOCKED",
                error_message=f"Target '{target_file}' escapes workspace '{root_dir}'.",
                remediation_steps=[
                    "Use a relative path strictly inside the target workspace.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="blocked_by_guardrail",
                actual_result=resp,
            )
            return resp

        if target_file.exists() and not validated.overwrite:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"File '{validated.relative_file_path}' already exists and overwrite=False.",
                error_code="FILE_ALREADY_EXISTS",
                error_message=f"Refusing to overwrite existing file '{target_file}'.",
                remediation_steps=[
                    "Set `overwrite=True` if you intend to replace the existing file.",
                    "Or choose a different `relative_file_path`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(validated.content, encoding="utf-8")
        line_count = len(validated.content.splitlines())

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Wrote '{validated.relative_file_path}' "
                f"({len(validated.content)} bytes, {line_count} lines) in '{root_dir.name}'."
            ),
            data={
                "workspace_path": str(root_dir),
                "relative_file_path": validated.relative_file_path,
                "absolute_file_path": str(target_file),
                "bytes_written": len(validated.content.encode("utf-8")),
                "line_count": line_count,
                "artifact_purpose": validated.artifact_purpose,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def synthesize_cross_project_terraform_module(
    workspace_path: str,
    target_gcp_project_id: str,
    resource_HCL: str,
    region: str = "us-central1",
    module_filename: str = "factory_resources.tf",
    run_terraform_validate: bool = True,
) -> dict[str, Any]:
    """Synthesizes and validates Terraform HCL resources for a target GCP project.

    Purpose:
        Enables the Software Builder Agent (`software_builder_agent`) to stand up
        GCP infrastructure in local or external projects via Terraform. Writes
        the HCL manifest into `<workspace_path>/terraform/<module_filename>` and
        runs `terraform fmt` (and optional `terraform validate`).

    Args:
        workspace_path: Target workspace path where `terraform/` resides.
        target_gcp_project_id: Lowercase GCP project ID (e.g., `'l200-509515'`).
        resource_HCL: Valid Terraform HCL resource/data/output blocks.
        region: Default GCP region (e.g., `'us-central1'`).
        module_filename: Filename ending in `.tf` inside `terraform/`.
        run_terraform_validate: Whether to run `terraform fmt` and `validate`.

    Returns:
        A serialized `GuidedToolResponse` dictionary with formatting/validation
        results or actionable HCL syntax recovery guidance.
    """
    tool_name = "synthesize_cross_project_terraform_module"
    raw_args = {
        "workspace_path": workspace_path,
        "target_gcp_project_id": target_gcp_project_id,
        "resource_HCL": resource_HCL,
        "region": region,
        "module_filename": module_filename,
        "run_terraform_validate": run_terraform_validate,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="software_builder_agent",
        intended_arguments={
            **raw_args,
            "resource_HCL": f"<{len(resource_HCL)} bytes HCL>",
        },
        rationale=f"Synthesize Terraform module '{module_filename}' for project '{target_gcp_project_id}'",
    )

    with DEFAULT_TELEMETRY.start_span(
        tool_name,
        attributes={
            "workspace_path": workspace_path,
            "target_gcp_project_id": target_gcp_project_id,
            "module_filename": module_filename,
        },
    ):
        try:
            validated = SynthesizeTerraformModuleInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid Terraform synthesis arguments.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Ensure `target_gcp_project_id` is strictly lowercase (e.g., 'l200-509515').",
                    "Ensure `module_filename` ends with '.tf' and contains no path separators.",
                    "Provide valid HCL resource blocks in `resource_HCL`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        root_dir = Path(validated.workspace_path).expanduser().resolve()
        tf_dir = root_dir / "terraform"
        tf_dir.mkdir(parents=True, exist_ok=True)
        target_tf_file = tf_dir / validated.module_filename
        target_tf_file.write_text(validated.resource_HCL, encoding="utf-8")

        tf_bin = _find_terraform_binary(root_dir)
        fmt_passed = True
        validate_passed = True
        validation_output = "Validation skipped or terraform binary not required."

        if validated.run_terraform_validate and tf_bin:
            fmt_res = subprocess.run(
                [tf_bin, f"-chdir={tf_dir}", "fmt"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            fmt_passed = fmt_res.returncode == 0
            if not fmt_passed:
                resp = GuidedToolResponse(
                    status=ToolExecutionStatus.ERROR,
                    tool_name=tool_name,
                    summary=f"Terraform HCL syntax error in '{validated.module_filename}'.",
                    error_code="TERRAFORM_HCL_SYNTAX_ERROR",
                    error_message=fmt_res.stderr.strip() or fmt_res.stdout.strip(),
                    remediation_steps=[
                        "Inspect the HCL syntax error line reported in `error_message`.",
                        "Ensure all resource blocks have matching braces `{}` and quoted strings.",
                        "Re-invoke `synthesize_cross_project_terraform_module` with corrected HCL.",
                    ],
                    retryable=True,
                ).model_dump(mode="json")
                DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                    correlation_id=corr_id,
                    outcome_status="error",
                    actual_result=resp,
                )
                return resp

            if (tf_dir / ".terraform").is_dir():
                val_res = subprocess.run(
                    [tf_bin, f"-chdir={tf_dir}", "validate", "-no-color"],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                validate_passed = val_res.returncode == 0
                validation_output = (
                    val_res.stdout.strip() or val_res.stderr.strip()
                )
                if not validate_passed:
                    resp = GuidedToolResponse(
                        status=ToolExecutionStatus.ERROR,
                        tool_name=tool_name,
                        summary=f"Terraform validation failed for '{validated.module_filename}'.",
                        error_code="TERRAFORM_VALIDATE_FAILED",
                        error_message=validation_output,
                        remediation_steps=[
                            "Check undeclared variables or provider references in `error_message`.",
                            "Ensure referenced variables exist in `terraform/variables.tf`.",
                            "Fix the HCL and call `synthesize_cross_project_terraform_module` again.",
                        ],
                        retryable=True,
                    ).model_dump(mode="json")
                    DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                        correlation_id=corr_id,
                        outcome_status="error",
                        actual_result=resp,
                    )
                    return resp
            else:
                validation_output = "Formatted cleanly with `terraform fmt` (provider init deferred to CI/CD)."

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Synthesized Terraform module 'terraform/{validated.module_filename}' "
                f"for GCP project '{validated.target_gcp_project_id}'."
            ),
            data={
                "workspace_path": str(root_dir),
                "terraform_file": str(target_tf_file),
                "target_gcp_project_id": validated.target_gcp_project_id,
                "region": validated.region,
                "terraform_fmt_passed": fmt_passed,
                "terraform_validate_passed": validate_passed,
                "validation_output": validation_output,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp
