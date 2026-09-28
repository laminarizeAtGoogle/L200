---
okf_version: "1.0"
entry_id: "deployer-sa"
entry_name: "Deployer Service Account (github-terraform-deployer)"
category: "deployed_gcp_assets"
sub_category: "iam"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Security Architecture / IAM Team"
dendrite_node_id: "deployer_sa"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Deployed GCP Asset): Deployer Service Account (github-terraform-deployer)

## 1. Executive Summary & Purpose
The `github-terraform-deployer` service account is the privileged deployment identity in Google Cloud. It is impersonated by GitHub Actions via Workload Identity Federation (WIF) and possesses the minimum necessary IAM permissions to manage Compute Engine resources and read/write remote Terraform state.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `gcp_iam_boundary`
- **Inbound Connections**:
  - `wif_pool`: Impersonated by GitHub Actions runners holding valid federated tokens.
- **Outbound Connections**:
  - `gcs_tfstate`: Reads and writes remote Terraform state.
  - `vpc_network`, `firewall_rules`, `compute_vm`: Executes Compute Engine API calls.
- **Trust Boundary & Security Classification**: Zero-Key Identity. No downloadable `.json` keys exist.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Provisioner: [`scripts/setup-argolis-github-wif.sh`](../../../scripts/setup-argolis-github-wif.sh)
- **Principal Email**:
  `github-terraform-deployer@<PROJECT_ID>.iam.gserviceaccount.com`
- **IAM Roles Granted**:
  - `roles/compute.admin`: Full administration of Compute Engine instances, networks, and firewalls.
  - `roles/storage.objectAdmin`: Read, write, and lock state objects in the remote GCS state bucket.
  - `roles/iam.workloadIdentityUser`: Bound to WIF pool subject.

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Automated by `./scripts/setup-argolis-github-wif.sh`.
- **Verification & Health Checks**:
  ```bash
  gcloud iam service-accounts describe github-terraform-deployer@<PROJECT_ID>.iam.gserviceaccount.com
  gcloud projects get-iam-policy <PROJECT_ID> --filter="bindings.members:github-terraform-deployer"
  ```
- **Failure Modes & Blast Radius**:
  - Missing IAM role bindings cause Terraform apply to fail mid-execution with `403 Forbidden`.
- **Recovery & Troubleshooting**:
  - Re-run `setup-argolis-github-wif.sh` or check IAM policy bindings via Cloud Console.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `deployer_sa` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - WIF Pool: [`deployed_gcp_assets/wif-pool.md`](wif-pool.md)
  - Reader SA: [`deployed_gcp_assets/reader-sa.md`](reader-sa.md)
  - State Bucket: [`deployed_gcp_assets/gcs-tfstate.md`](gcs-tfstate.md)
  - Apply Pipeline: [`codebase/gha-apply.md`](../codebase/gha-apply.md)
