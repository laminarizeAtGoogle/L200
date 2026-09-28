---
okf_version: "1.0"
component_id: "reader-sa"
component_name: "Read-Only Service Account (cloudtop-agent-reader)"
category: "IAM & Security"
tier: "Tier 2 - Operational"
status: "active"
owner: "Security Architecture / Zero-Privilege Team"
dendrite_node_id: "reader_sa"
last_verified: "2026-09-28"
---

# OKF: Read-Only Service Account (cloudtop-agent-reader)

## 1. Executive Summary & Purpose
The `cloudtop-agent-reader` service account establishes a hard zero-privilege security boundary at the IAM layer on Cloudtop workstations. Local coding agents and scripts impersonate this service account to inspect live GCP state without possessing any rights to alter, delete, or create cloud resources.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `gcp_iam_boundary`
- **Inbound Connections**:
  - `cloudtop_shell`: Impersonated via `gcloud config set auth/impersonate_service_account`.
- **Outbound Connections**:
  - `argolis_project`: Read-only queries to Compute Engine and Cloud Storage APIs.
- **Trust Boundary & Security Classification**: Zero-Privilege Sandbox Boundary. Prevents privilege escalation from autonomous local agents.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Provisioner: [`scripts/provision-argolis-env.sh`](../../scripts/provision-argolis-env.sh)
- **Principal Email**:
  `cloudtop-agent-reader@<PROJECT_ID>.iam.gserviceaccount.com`
- **IAM Roles Granted**:
  - `roles/viewer`: Global read-only access to GCP project metadata and resource states.
  - `roles/storage.objectViewer`: Read-only inspection of Cloud Storage objects.
  - Explicitly **NO** admin or mutation roles.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./scripts/provision-argolis-env.sh --project <PROJECT_ID>
  ```
- **Activating Impersonation on Cloudtop**:
  ```bash
  gcloud config set auth/impersonate_service_account cloudtop-agent-reader@<PROJECT_ID>.iam.gserviceaccount.com
  ```
- **Verification & Health Checks**:
  ```bash
  gcloud auth list
  ./bin/argolis status
  # Verify mutation is blocked:
  gcloud compute instances stop <NAME> # Expected: 403 Forbidden
  ```
- **Failure Modes & Blast Radius**:
  - If impersonation expires or service account is deleted, local read-only commands will fail. Production infrastructure remains completely unaffected.

## 5. References & Linked Assets
- Dendrite Diagram Node: `reader_sa` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Security Specification: [`scripts/README.md`](../../scripts/README.md)
- Related OKF Entries: [`deployer-sa`](deployer-sa.md), [`cloudtop-shell`](cloudtop-shell.md)
