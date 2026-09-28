---
okf_version: "1.0"
entry_id: "gha-apply"
entry_name: "GitHub Actions: Terraform Apply Pipeline"
category: "codebase"
sub_category: "cicd"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "DevOps & CI/CD Team"
dendrite_node_id: "gha_apply"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): GitHub Actions Terraform Apply Pipeline

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
  - Workflow file: [`.github/workflows/terraform-apply.yml`](../../../.github/workflows/terraform-apply.yml)
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
- **Dendrite Diagram Node**: `gha_apply` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Plan Pipeline: [`codebase/gha-plan.md`](gha-plan.md)
  - WIF Pool: [`deployed_gcp_assets/wif-pool.md`](../deployed_gcp_assets/wif-pool.md)
  - Deployer SA: [`deployed_gcp_assets/deployer-sa.md`](../deployed_gcp_assets/deployer-sa.md)
  - Remote State: [`deployed_gcp_assets/gcs-tfstate.md`](../deployed_gcp_assets/gcs-tfstate.md)
  - Terraform Modules: [`codebase/terraform-infrastructure-modules.md`](terraform-infrastructure-modules.md)
