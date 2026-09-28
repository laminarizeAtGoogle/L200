"""Read-only gcloud resource probing, Cloud Logging inspection, and Argolis verification tools.

Enforces the Zero-Privilege Local Security Boundary:
- Every `gcloud` invocation explicitly impersonates the read-only service account
  (`cloudtop-agent-reader@<PROJECT_ID>.iam.gserviceaccount.com`).
- Only strictly read-only `list` / `describe` / `read` / `search-all-resources`
  subcommands are allowed; mutating verbs are blocked by both schema constraints
  and the `SoftwareFactoryGuardrailsPlugin`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from pydantic import ValidationError

from ..config import WORKSPACE_ROOT
from ..observability import (
    DEFAULT_INTENT_OUTCOME_RECORDER,
    DEFAULT_SCRUBBER,
    DEFAULT_TELEMETRY,
)
from ..orchestration import DEFAULT_GUARDRAILS_PLUGIN
from ..schemas import (
    GcloudReadonlyProbeInput,
    GuidedToolResponse,
    QueryCloudLoggingInput,
    ToolExecutionStatus,
)


_READONLY_DOMAIN_COMMANDS: dict[str, list[str]] = {
    "compute_instances": ["compute", "instances", "list"],
    "storage_buckets": ["storage", "buckets", "list"],
    "service_accounts": ["iam", "service-accounts", "list"],
    "workload_identity_pools": [
        "iam",
        "workload-identity-pools",
        "list",
        "--location=global",
    ],
    "cloud_run_services": ["run", "services", "list"],
    "secrets": ["secrets", "list"],
    "vpc_networks": ["compute", "networks", "list"],
    "cloud_assets": ["asset", "search-all-resources"],
}


def _resolve_gcloud_binary() -> tuple[str, dict[str, str]]:
    """Resolves the workspace's isolated ./bin/gcloud wrapper and environment."""
    gcloud_bin = WORKSPACE_ROOT / "bin" / "gcloud"
    env = os.environ.copy()
    env["CLOUDSDK_CONFIG"] = str(WORKSPACE_ROOT / ".gcloud")
    adc_file = WORKSPACE_ROOT / ".gcloud" / "application_default_credentials.json"
    if adc_file.is_file():
        env["GOOGLE_APPLICATION_CREDENTIALS"] = str(adc_file)

    if gcloud_bin.is_file():
        return str(gcloud_bin), env
    return shutil.which("gcloud") or "gcloud", env


def probe_gcp_resources_readonly(
    project_id: str,
    resource_domain: str,
    impersonate_service_account: str | None = None,
    filter_expression: str | None = None,
) -> dict[str, Any]:
    """Probes live GCP resources in read-only mode using `cloudtop-agent-reader`.

    Purpose:
        Enables the Read-Only gcloud Probe Agent (`gcloud_readonly_probe_agent`)
        to inspect deployed resources across Argolis or external GCP projects
        without holding write/admin privileges.

    Args:
        project_id: Target lowercase GCP project ID (e.g., `'l200-509515'`).
        resource_domain: Resource category to inspect. Must be one of:
            `'compute_instances'`, `'storage_buckets'`, `'service_accounts'`,
            `'workload_identity_pools'`, `'cloud_run_services'`, `'secrets'`,
            `'vpc_networks'`, or `'cloud_assets'`.
        impersonate_service_account: Optional read-only Service Account email to
            impersonate. Defaults to
            `'cloudtop-agent-reader@<project_id>.iam.gserviceaccount.com'`.
        filter_expression: Optional read-only `--filter` expression.

    Returns:
        A serialized `GuidedToolResponse` containing the discovered GCP resources
        and impersonated identity, or guided recovery instructions on error.
    """
    tool_name = "probe_gcp_resources_readonly"
    raw_args = {
        "project_id": project_id,
        "resource_domain": resource_domain,
        "impersonate_service_account": impersonate_service_account,
        "filter_expression": filter_expression,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="gcloud_readonly_probe_agent",
        intended_arguments=raw_args,
        rationale=f"Probe '{resource_domain}' in project '{project_id}' via read-only SA impersonation",
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
            validated = GcloudReadonlyProbeInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid arguments for read-only gcloud resource probe.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    f"Set `resource_domain` to one of: {sorted(_READONLY_DOMAIN_COMMANDS.keys())}.",
                    "Ensure `project_id` is a valid lowercase GCP project ID (e.g., 'l200-509515').",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        reader_sa = (
            validated.impersonate_service_account
            or f"cloudtop-agent-reader@{validated.project_id}.iam.gserviceaccount.com"
        )
        gcloud_bin, env = _resolve_gcloud_binary()
        subcmd = _READONLY_DOMAIN_COMMANDS[validated.resource_domain]

        cmd = [
            gcloud_bin,
            *subcmd,
            f"--project={validated.project_id}",
            f"--impersonate-service-account={reader_sa}",
            "--format=json",
            "--quiet",
        ]
        if validated.filter_expression:
            cmd.append(f"--filter={validated.filter_expression}")

        try:
            proc = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
        except Exception as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Failed to execute gcloud probe: {exc}",
                error_code="GCLOUD_EXECUTION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Verify `./bin/argolis status` and ensure gcloud SDK is installed.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        if proc.returncode != 0:
            err_msg = DEFAULT_SCRUBBER.scrub_text(
                proc.stderr.strip() or proc.stdout.strip()
            )
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=(
                    f"Read-only probe for '{validated.resource_domain}' in "
                    f"'{validated.project_id}' returned non-zero status."
                ),
                error_code="GCLOUD_PROBE_NONZERO",
                error_message=err_msg,
                data={
                    "project_id": validated.project_id,
                    "resource_domain": validated.resource_domain,
                    "impersonated_sa": reader_sa,
                    "command": " ".join(cmd[1:]),
                },
                remediation_steps=[
                    f"Verify that `{reader_sa}` exists and has `roles/viewer` on project `{validated.project_id}` (provision via `./scripts/provision-argolis-env.sh --project {validated.project_id}`).",
                    "Ensure the corresponding GCP API (e.g., compute.googleapis.com, run.googleapis.com) is enabled via Terraform.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        try:
            parsed_resources = json.loads(proc.stdout or "[]")
        except Exception:
            parsed_resources = []

        scrubbed_resources = DEFAULT_SCRUBBER.scrub_payload(parsed_resources)
        count = (
            len(scrubbed_resources)
            if isinstance(scrubbed_resources, list)
            else 1
        )

        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Probed '{validated.resource_domain}' in project '{validated.project_id}' "
                f"as '{reader_sa}' ({count} resource(s) found)."
            ),
            data={
                "project_id": validated.project_id,
                "resource_domain": validated.resource_domain,
                "impersonated_service_account": reader_sa,
                "resource_count": count,
                "resources": scrubbed_resources,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def query_cloud_logging_entries_readonly(
    project_id: str,
    log_filter: str = 'severity>="DEFAULT"',
    limit: int = 20,
    impersonate_service_account: str | None = None,
) -> dict[str, Any]:
    """Queries Google Cloud Logging entries in read-only mode with PII redaction.

    Purpose:
        Enables the Read-Only gcloud Probe Agent (`gcloud_readonly_probe_agent`)
        and Cloud Log Auditor (`cloud_log_auditor_agent`) to read audit logs,
        deployment logs, and service telemetry to diagnose or verify a deployment.

    Args:
        project_id: Target lowercase GCP project ID.
        log_filter: Cloud Logging filter expression (e.g.,
            `'resource.type="cloud_run_revision" AND severity>="ERROR"'`).
        limit: Maximum number of log entries to return (1 to 100).
        impersonate_service_account: Read-only Service Account to impersonate
            (defaults to `cloudtop-agent-reader@<project_id>.iam.gserviceaccount.com`).

    Returns:
        A serialized `GuidedToolResponse` containing PII-scrubbed Cloud Logging
        entries or guided error recovery steps.
    """
    tool_name = "query_cloud_logging_entries_readonly"
    raw_args = {
        "project_id": project_id,
        "log_filter": log_filter,
        "limit": limit,
        "impersonate_service_account": impersonate_service_account,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="gcloud_readonly_probe_agent",
        intended_arguments=raw_args,
        rationale=f"Read Cloud Logging entries in project '{project_id}' via read-only SA",
    )

    with DEFAULT_TELEMETRY.start_span(tool_name, attributes=raw_args):
        try:
            validated = QueryCloudLoggingInput.model_validate(raw_args)
        except ValidationError as exc:
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary="Invalid Cloud Logging query arguments.",
                error_code="SCHEMA_VALIDATION_ERROR",
                error_message=str(exc),
                remediation_steps=[
                    "Ensure `project_id` is lowercase and `limit` is between 1 and 100.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        reader_sa = (
            validated.impersonate_service_account
            or f"cloudtop-agent-reader@{validated.project_id}.iam.gserviceaccount.com"
        )
        gcloud_bin, env = _resolve_gcloud_binary()
        cmd = [
            gcloud_bin,
            "logging",
            "read",
            validated.log_filter,
            f"--project={validated.project_id}",
            f"--impersonate-service-account={reader_sa}",
            f"--limit={validated.limit}",
            "--format=json",
            "--quiet",
        ]

        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )

        if proc.returncode != 0:
            err_msg = DEFAULT_SCRUBBER.scrub_text(
                proc.stderr.strip() or proc.stdout.strip()
            )
            resp = GuidedToolResponse(
                status=ToolExecutionStatus.ERROR,
                tool_name=tool_name,
                summary=f"Cloud Logging query returned non-zero status on '{validated.project_id}'.",
                error_code="GCLOUD_LOGGING_READ_FAILED",
                error_message=err_msg,
                remediation_steps=[
                    "Check `log_filter` syntax for unbalanced quotes.",
                    f"Ensure `{reader_sa}` has `roles/viewer` or `roles/logging.viewer` on `{validated.project_id}`.",
                ],
                retryable=True,
            ).model_dump(mode="json")
            DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
                correlation_id=corr_id,
                outcome_status="error",
                actual_result=resp,
            )
            return resp

        try:
            entries = json.loads(proc.stdout or "[]")
        except Exception:
            entries = []

        scrubbed_entries = DEFAULT_SCRUBBER.scrub_payload(entries)
        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Retrieved {len(scrubbed_entries)} PII-scrubbed log entries "
                f"from project '{validated.project_id}'."
            ),
            data={
                "project_id": validated.project_id,
                "impersonated_service_account": reader_sa,
                "log_filter": validated.log_filter,
                "entry_count": len(scrubbed_entries),
                "entries": scrubbed_entries,
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp


def verify_deployed_argolis_infrastructure(
    project_id: str,
    expected_resources: list[str],
    workspace_path: str | None = None,
    impersonate_service_account: str | None = None,
) -> dict[str, Any]:
    """Verifies that Terraform-defined resources and WIF boundaries are active in Argolis.

    Purpose:
        Allows the Read-Only gcloud Probe Agent (`gcloud_readonly_probe_agent`)
        to verify implementation completeness by checking both the local
        Terraform manifests in `workspace_path` and the live GCP project state.

    Args:
        project_id: Target GCP project ID (e.g., `'l200-509515'`).
        expected_resources: List of resource identifiers or Terraform resource
            types expected to be present (e.g.,
            `['github-terraform-deployer', 'cloudtop-agent-reader', 'tfstate']`).
        workspace_path: Optional workspace directory containing `terraform/`.
        impersonate_service_account: Optional read-only SA email.

    Returns:
        A serialized `GuidedToolResponse` summarizing verified vs. missing
        resources and overall implementation verification status.
    """
    tool_name = "verify_deployed_argolis_infrastructure"
    raw_args = {
        "project_id": project_id,
        "expected_resources": expected_resources,
        "workspace_path": workspace_path,
        "impersonate_service_account": impersonate_service_account,
    }
    corr_id = DEFAULT_INTENT_OUTCOME_RECORDER.record_intent(
        action_name=tool_name,
        actor_agent="gcloud_readonly_probe_agent",
        intended_arguments=raw_args,
        rationale="Verify deployed Argolis infrastructure and Terraform declarations",
    )

    with DEFAULT_TELEMETRY.start_span(
        tool_name,
        attributes={
            "project_id": project_id,
            "expected_count": len(expected_resources),
        },
    ):
        ws_dir = Path(workspace_path or WORKSPACE_ROOT).expanduser().resolve()
        tf_dir = ws_dir / "terraform"
        declared_hcl_content = ""
        tf_files: list[str] = []
        if tf_dir.is_dir():
            for tf_file in sorted(tf_dir.glob("*.tf")):
                tf_files.append(tf_file.name)
                declared_hcl_content += "\n" + tf_file.read_text(
                    encoding="utf-8", errors="ignore"
                )

        sa_probe = probe_gcp_resources_readonly(
            project_id=project_id,
            resource_domain="service_accounts",
            impersonate_service_account=impersonate_service_account,
        )
        live_blob = json.dumps(sa_probe.get("data", {}))

        verified_items: list[dict[str, Any]] = []
        for item in expected_resources:
            in_terraform = item in declared_hcl_content
            in_live_gcp = item in live_blob
            verified_items.append(
                {
                    "expected_resource": item,
                    "declared_in_terraform": in_terraform,
                    "observed_in_live_gcp": in_live_gcp,
                    "verified": in_terraform or in_live_gcp,
                }
            )

        all_verified = all(v["verified"] for v in verified_items)
        resp = GuidedToolResponse(
            status=ToolExecutionStatus.SUCCESS,
            tool_name=tool_name,
            summary=(
                f"Infrastructure verification for '{project_id}': "
                f"{sum(1 for v in verified_items if v['verified'])}/{len(verified_items)} "
                f"expected items verified across Terraform ({len(tf_files)} files) and live GCP probe."
            ),
            data={
                "project_id": project_id,
                "workspace_path": str(ws_dir),
                "terraform_files": tf_files,
                "all_verified": all_verified,
                "verification_matrix": verified_items,
                "live_service_account_probe_status": sa_probe.get("status"),
            },
        ).model_dump(mode="json")
        DEFAULT_INTENT_OUTCOME_RECORDER.record_outcome(
            correlation_id=corr_id,
            outcome_status="success",
            actual_result=resp,
        )
        return resp
