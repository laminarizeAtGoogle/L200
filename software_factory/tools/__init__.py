"""Export all schema-validated ADK tools for the A2A Software Factory."""

from .gcloud_probe_tools import (
    probe_gcp_resources_readonly,
    query_cloud_logging_entries_readonly,
    verify_deployed_argolis_infrastructure,
)
from .cloud_env_tools import (
    query_cloud_logging_readonly,
    query_cloud_run_services_readonly,
    query_compute_instances_readonly,
    query_iam_policy_readonly,
    query_storage_buckets_readonly,
)
from .git_wif_tools import (
    commit_workspace_changes_with_context,
    configure_cross_project_wif_federation,
    create_isolated_feature_branch_from_main,
    open_pull_request_for_terraform_apply,
    request_human_approval_for_high_stakes_action,
)
from .workspace_tools import (
    generate_workspace_software_artifact,
    inspect_target_workspace_state,
    synthesize_cross_project_terraform_module,
)

READONLY_CLOUD_TOOLS = [
    query_compute_instances_readonly,
    query_cloud_run_services_readonly,
    query_storage_buckets_readonly,
    query_iam_policy_readonly,
    query_cloud_logging_readonly,
    probe_gcp_resources_readonly,
    verify_deployed_argolis_infrastructure,
]

ALL_FACTORY_TOOLS = [
    inspect_target_workspace_state,
    generate_workspace_software_artifact,
    synthesize_cross_project_terraform_module,
    create_isolated_feature_branch_from_main,
    commit_workspace_changes_with_context,
    configure_cross_project_wif_federation,
    open_pull_request_for_terraform_apply,
    request_human_approval_for_high_stakes_action,
    probe_gcp_resources_readonly,
    query_cloud_logging_entries_readonly,
    verify_deployed_argolis_infrastructure,
    query_compute_instances_readonly,
    query_cloud_run_services_readonly,
    query_storage_buckets_readonly,
    query_iam_policy_readonly,
    query_cloud_logging_readonly,
]

__all__ = [
    "ALL_FACTORY_TOOLS",
    "READONLY_CLOUD_TOOLS",
    "commit_workspace_changes_with_context",
    "configure_cross_project_wif_federation",
    "create_isolated_feature_branch_from_main",
    "generate_workspace_software_artifact",
    "inspect_target_workspace_state",
    "open_pull_request_for_terraform_apply",
    "probe_gcp_resources_readonly",
    "query_cloud_logging_entries_readonly",
    "query_cloud_logging_readonly",
    "query_cloud_run_services_readonly",
    "query_compute_instances_readonly",
    "query_iam_policy_readonly",
    "query_storage_buckets_readonly",
    "request_human_approval_for_high_stakes_action",
    "synthesize_cross_project_terraform_module",
    "verify_deployed_argolis_infrastructure",
]
