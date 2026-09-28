---
okf_version: "1.0"
component_id: "gha-apply"
component_name: "GitHub Actions: Terraform Apply Pipeline"
category: "CI/CD"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "DevOps & CI/CD Team"
dendrite_node_id: "gha_apply"
last_verified: "2026-09-28"
---

# OKF: GitHub Actions Terraform Apply Pipeline

## 1. Executive Summary & Purpose
The Terraform Apply Pipeline is the continuous deployment pipeline executed upon merge to `main`. It initializes against the remote GCS state, verifies plan consistency, and executes `terraform apply -auto-approve` to provision and synchronize live Argolis infrastructure without manual intervention.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `github_platform`
- **Inbound Connections**:
  - `github_repo`: Triggered by `push` events to `main` on paths `terraform/**`.
- **Outbound Connections**:
  - `wif_pool`: Acquires ephemeral Google OAuth2 access token via OIDC.
  - `gcs_tfstate`: Reads and writes `terraform.tfstate`.
  - `vpc_network`, `firewall_rules`, `compute_vm`: Mutates target GCP resources via Compute Engine APIs.
- **Trust Boundary & Security Classification**: Privileged deployment runner. Execution strictly gated to merged commits on `main`.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Workflow file: [`.github/workflows/terraform-apply.yml`](../../.github/workflows/terraform-apply.yml)
- **Protocols & Interfaces**: HTTPS / GCP REST APIs.
- **Concurrency & Locking**:
  - Concurrency group: `terraform-production` (`cancel-in-progress: false`).
  - GCS state locking prevents concurrent apply collisions.
- **Execution Command**:
  ```bash
  terraform apply -auto-approve -input=false
  ```

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Configured and managed via git in `.github/workflows/terraform-apply.yml`.
- **Verification & Health Checks**:
  - Check GitHub Actions execution logs under `Actions > Terraform Apply on Main Merge`.
- **Failure Modes & Blast Radius**:
  - Apply failure may leave Terraform state partially modified. Terraform state lock will prevent subsequent applies until resolved.
- **Recovery & Troubleshooting**:
  - If state lock is stuck: `terraform force-unlock <LOCK_ID>`.
  - Check Cloud Logging in Argolis project for IAM or quota errors.

## 5. References & Linked Assets
- Dendrite Diagram Node: `gha_apply` in [`docs/architecture_diagram.dendrite.yaml`](../architecture_diagram.dendrite.yaml)
- Related OKF Entries: [`gha-plan`](gha-plan.md), [`wif-pool`](wif-pool.md), [`deployer-sa`](deployer-sa.md), [`gcs-tfstate`](gcs-tfstate.md)
