"""Strict Read-Only Cloud Environment Query Tools.

Provides specialized read-only inspection tools for Google Cloud infrastructure:
1. Compute Engine VM instances (`query_compute_instances_readonly`)
2. Cloud Run v2 services (`query_cloud_run_services_readonly`)
3. GKE Kubernetes clusters (`query_gke_clusters_readonly`)
4. Cloud Storage bucket metadata (`query_storage_buckets_readonly`)
5. IAM policy bindings (`query_iam_policy_readonly`)
6. Cloud Logging audit & error logs (`query_cloud_logging_readonly`)

Guarantees:
- Strict zero-mutation enforcement: mutating verbs (create, delete, update) are impossible.
- Database query isolation: NO tools exist for querying Cloud SQL, Spanner, or Firestore data.
- Strict Pydantic v2 schemas (`extra="forbid"`) and guided error recovery.
"""

from __future__ import annotations

from typing import Any
from pydantic import ValidationError

from ..config import DEFAULT_CONFIG
from ..schemas import (
    GuidedToolResponse,
    QueryCloudLoggingInput,
    QueryCloudRunServicesInput,
    QueryComputeInstancesInput,
    QueryGkeClustersInput,
    QueryIamPolicyInput,
    QueryStorageBucketsInput,
    ToolExecutionStatus,
)
from .gcloud_probe_tools import (
    probe_gcp_resources_readonly,
    query_cloud_logging_entries_readonly,
)


def query_compute_instances_readonly(
    raw_input: dict[str, Any] | QueryComputeInstancesInput,
) -> dict[str, Any]:
    """Inspects Compute Engine virtual machine instances in the Google Cloud environment.

    Purpose:
        Queries Compute Engine API in read-only mode to retrieve active VM instances,
        machine types, internal/external IPs, statuses (RUNNING, STOPPED), and zones.

    Args:
        raw_input: Dictionary or QueryComputeInstancesInput containing:
            - project_id: Optional GCP project ID to query.
            - zone: Optional Compute Engine zone filter (e.g. 'us-central1-a').

    Returns:
        Serialized GuidedToolResponse containing the list of active VM instances,
        machine types, internal/external IPs, and statuses (RUNNING, STOPPED).

    Example:
        >>> result = query_compute_instances_readonly({"zone": "us-central1-a"})
        >>> print(result["status"])
        'success'
    """
    try:
        validated = (
            raw_input
            if isinstance(raw_input, QueryComputeInstancesInput)
            else QueryComputeInstancesInput.model_validate(raw_input)
        )
    except ValidationError as e:
        return GuidedToolResponse(
            status=ToolExecutionStatus.ERROR,
            tool_name="query_compute_instances_readonly",
            summary="Validation failed on compute instances query parameters.",
            error_code="VALIDATION_ERROR",
            error_message=str(e),
            remediation_steps=["Check that project_id and zone are valid strings."],
            retryable=True,
        ).model_dump(mode="json")

    project_id = validated.project_id or DEFAULT_CONFIG.project_id
    filter_exp = f"zone:{validated.zone}" if validated.zone else None
    return probe_gcp_resources_readonly(
        project_id=project_id,
        resource_domain="compute_instances",
        filter_expression=filter_exp,
    )


def query_cloud_run_services_readonly(
    raw_input: dict[str, Any] | QueryCloudRunServicesInput,
) -> dict[str, Any]:
    """Inspects Cloud Run v2 services deployed in the Google Cloud environment.

    Purpose:
        Queries Cloud Run Admin API in read-only mode to list deployed services,
        traffic allocations, latest revisions, and container image URIs.

    Args:
        raw_input: Dictionary or QueryCloudRunServicesInput containing:
            - project_id: Optional GCP project ID.
            - region: Optional region filter (e.g. 'us-central1').

    Returns:
        Serialized GuidedToolResponse containing active Cloud Run services, traffic allocations,
        service URLs, latest revisions, and container image URIs.

    Example:
        >>> result = query_cloud_run_services_readonly({"region": "us-central1"})
        >>> print(result["summary"])
    """
    try:
        validated = (
            raw_input
            if isinstance(raw_input, QueryCloudRunServicesInput)
            else QueryCloudRunServicesInput.model_validate(raw_input)
        )
    except ValidationError as e:
        return GuidedToolResponse(
            status=ToolExecutionStatus.ERROR,
            tool_name="query_cloud_run_services_readonly",
            summary="Validation error on Cloud Run query parameters.",
            error_code="VALIDATION_ERROR",
            error_message=str(e),
            remediation_steps=["Verify project_id and region format."],
            retryable=True,
        ).model_dump(mode="json")

    project_id = validated.project_id or DEFAULT_CONFIG.project_id
    filter_exp = f"region:{validated.region}" if validated.region else None
    return probe_gcp_resources_readonly(
        project_id=project_id,
        resource_domain="cloud_run_services",
        filter_expression=filter_exp,
    )


def query_storage_buckets_readonly(
    raw_input: dict[str, Any] | QueryStorageBucketsInput,
) -> dict[str, Any]:
    """Inspects Google Cloud Storage (GCS) bucket metadata and storage classes.

    Purpose:
        Queries Google Cloud Storage API in read-only mode to list bucket names,
        creation dates, locations, and storage classes without exposing object data.

    Args:
        raw_input: Dictionary or QueryStorageBucketsInput containing:
            - project_id: Optional GCP project ID.

    Returns:
        Serialized GuidedToolResponse containing bucket names, creation dates, locations,
        and storage classes (metadata only; object contents are never leaked).

    Example:
        >>> result = query_storage_buckets_readonly({})
    """
    try:
        validated = (
            raw_input
            if isinstance(raw_input, QueryStorageBucketsInput)
            else QueryStorageBucketsInput.model_validate(raw_input)
        )
    except ValidationError as e:
        return GuidedToolResponse(
            status=ToolExecutionStatus.ERROR,
            tool_name="query_storage_buckets_readonly",
            summary="Validation error on Storage Buckets query.",
            error_code="VALIDATION_ERROR",
            error_message=str(e),
            remediation_steps=["Verify project_id format."],
            retryable=True,
        ).model_dump(mode="json")

    project_id = validated.project_id or DEFAULT_CONFIG.project_id
    return probe_gcp_resources_readonly(
        project_id=project_id,
        resource_domain="storage_buckets",
    )


def query_iam_policy_readonly(
    raw_input: dict[str, Any] | QueryIamPolicyInput,
) -> dict[str, Any]:
    """Inspects IAM roles and service account bindings in the Google Cloud environment.

    Purpose:
        Queries Google Cloud IAM API in read-only mode to retrieve service accounts,
        assigned role grants, and workload identity pool configurations.

    Args:
        raw_input: Dictionary or QueryIamPolicyInput containing:
            - project_id: Optional GCP project ID.

    Returns:
        Serialized GuidedToolResponse containing service accounts, IAM role grants, and workload identity pools.

    Example:
        >>> result = query_iam_policy_readonly({})
    """
    try:
        validated = (
            raw_input
            if isinstance(raw_input, QueryIamPolicyInput)
            else QueryIamPolicyInput.model_validate(raw_input)
        )
    except ValidationError as e:
        return GuidedToolResponse(
            status=ToolExecutionStatus.ERROR,
            tool_name="query_iam_policy_readonly",
            summary="Validation error on IAM query.",
            error_code="VALIDATION_ERROR",
            error_message=str(e),
            remediation_steps=["Verify project_id format."],
            retryable=True,
        ).model_dump(mode="json")

    project_id = validated.project_id or DEFAULT_CONFIG.project_id
    return probe_gcp_resources_readonly(
        project_id=project_id,
        resource_domain="service_accounts",
    )


def query_cloud_logging_readonly(
    raw_input: dict[str, Any] | QueryCloudLoggingInput,
) -> dict[str, Any]:
    """Queries Cloud Logging for recent system logs, container errors, and diagnostic traces.

    Purpose:
        Queries Google Cloud Logging API in read-only mode to retrieve log entries,
        severity levels, and timestamps for application and system troubleshooting.

    Args:
        raw_input: Dictionary or QueryCloudLoggingInput containing:
            - log_filter: Optional Cloud Logging filter expression.
            - severity: Optional severity threshold ('DEFAULT', 'INFO', 'WARNING', 'ERROR').
            - max_entries: Number of entries to retrieve (1-100).
            - target_project_id: Optional GCP project ID.

    Returns:
        Serialized GuidedToolResponse containing log entries with timestamps, severity, and log messages.

    Example:
        >>> result = query_cloud_logging_readonly({"severity": "ERROR", "max_entries": 10})
    """
    try:
        validated = (
            raw_input
            if isinstance(raw_input, QueryCloudLoggingInput)
            else QueryCloudLoggingInput.model_validate(raw_input)
        )
    except ValidationError as e:
        return GuidedToolResponse(
            status=ToolExecutionStatus.ERROR,
            tool_name="query_cloud_logging_readonly",
            summary="Validation error on Cloud Logging query.",
            error_code="VALIDATION_ERROR",
            error_message=str(e),
            remediation_steps=["Verify log_filter and severity."],
            retryable=True,
        ).model_dump(mode="json")

    project_id = validated.target_project_id or DEFAULT_CONFIG.project_id
    filter_exp = validated.log_filter or f'severity>="{validated.severity}"'
    return query_cloud_logging_entries_readonly(
        project_id=project_id,
        log_filter=filter_exp,
        limit=validated.max_entries,
    )
