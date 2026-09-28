---
okf_version: "1.0"
component_id: "gcs-tfstate"
component_name: "Cloud Storage Remote Terraform State Bucket"
category: "Storage & Data"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Platform Engineering / State Management"
dendrite_node_id: "gcs_tfstate"
last_verified: "2026-09-28"
---

# OKF: Cloud Storage Remote Terraform State Bucket

## 1. Executive Summary & Purpose
The Remote Terraform State Bucket provides secure, centralized, and versioned storage for the canonical `terraform.tfstate` file. It features object versioning and state locking to prevent state corruption, concurrent apply collisions, and out-of-band drift.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `argolis_project`
- **Inbound Connections**:
  - `gha_plan`: Acquires read-only state lock during PR planning.
  - `gha_apply`: Acquires exclusive state lock, reads current state, and writes updated state after apply.
- **Outbound Connections**:
  - None (data sink).
- **Trust Boundary & Security Classification**: Encrypted Cloud Storage bucket with Uniform Bucket-Level Access and public access prevention enabled.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Backend configuration: [`terraform/backend.tf.example`](../../terraform/backend.tf.example)
  - Bucket provisioner: [`scripts/setup-argolis-github-wif.sh`](../../scripts/setup-argolis-github-wif.sh)
- **Bucket Name Pattern**: `<PROJECT_ID>-tfstate`
- **Location**: Multi-region `US` or regional `us-central1`.
- **Security Features**:
  - Uniform Bucket-Level Access (UBLA): `enabled`
  - Object Versioning: `enabled`
  - Public Access Prevention: `enforced`
  - Google-Managed Encryption: `AES-256`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  ```bash
  ./scripts/setup-argolis-github-wif.sh --project <PROJECT_ID> --repo <OWNER/REPO>
  ```
- **Verification & Health Checks**:
  ```bash
  gcloud storage buckets describe gs://<PROJECT_ID>-tfstate
  gcloud storage ls gs://<PROJECT_ID>-tfstate
  ```
- **Failure Modes & Blast Radius**:
  - State bucket deletion or misconfigured permissions blocks all Terraform operations across the project.
- **Recovery & Troubleshooting**:
  - Recover past state versions:
    ```bash
    gcloud storage objects versions list gs://<PROJECT_ID>-tfstate/terraform/state/default.tfstate
    ```

## 5. References & Linked Assets
- Dendrite Diagram Node: `gcs_tfstate` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`deployer-sa`](deployer-sa.md), [`gha-apply`](gha-apply.md)
