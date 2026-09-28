---
okf_version: "1.0"
entry_id: "gha-plan"
entry_name: "GitHub Actions: Terraform Plan Pipeline"
category: "codebase"
sub_category: "cicd"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "DevOps & CI/CD Team"
dendrite_node_id: "gha_plan"
discovered_by: "static_analysis"
last_verified: "2026-09-28"
---

# OKF (Codebase): GitHub Actions Terraform Plan Pipeline

## 1. Executive Summary & Purpose
The Terraform Plan Pipeline is an automated GitHub Actions workflow triggered whenever a pull request is opened or updated targeting the `main` branch. It validates formatting, initializes Terraform with remote GCS state, verifies syntax, and generates a speculative infrastructure execution plan.

## 2. Architectural Role & Dendrite Topology
- **Subsystem & Boundary**: `github_platform`
- **Inbound Connections**:
  - `github_repo`: Triggered by `pull_request` events targeting `main` on paths `terraform/**`.
- **Outbound Connections**:
  - `wif_pool`: Authenticates to GCP via OIDC token exchange.
  - `gcs_tfstate`: Reads remote `terraform.tfstate` (read-only locking).
- **Trust Boundary & Security Classification**: Ephemeral GitHub-hosted runner (`ubuntu-latest`). Read-only infrastructure planning scope.

## 3. Technical Specifications & Configuration
- **Implementation Path(s)**:
  - Workflow definition: [`.github/workflows/terraform-plan.yml`](../../../.github/workflows/terraform-plan.yml)
- **Protocols & Interfaces**: HTTPS / GitHub Actions runner runtime.
- **Workflow Steps**:
  1. `actions/checkout@v4`
  2. `google-github-actions/auth@v2` (WIF exchange)
  3. `hashicorp/setup-terraform@v3`
  4. `terraform fmt -check`
  5. `terraform init`
  6. `terraform validate`
  7. `terraform plan -no-color`
- **Required Secrets & Variables**:
  - `secrets.GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `secrets.GCP_SERVICE_ACCOUNT`
  - `secrets.TF_STATE_BUCKET`
  - `vars.GCP_PROJECT_ID`

## 4. Operational Runbook & Lifecycle
- **Provisioning & Deployment**:
  - Committed in `.github/workflows/terraform-plan.yml`.
- **Verification & Health Checks**:
  - Inspect GitHub PR "Checks" tab for status of `terraform-plan`.
- **Failure Modes & Blast Radius**:
  - Workflow failure blocks pull request merge into `main`. Does not mutate live infrastructure.
- **Recovery & Troubleshooting**:
  - Inspect failed job logs on GitHub Actions; verify WIF provider permissions and GCS state bucket access.

## 5. References & Linked Assets
- **Dendrite Diagram Node**: `gha_plan` in [`docs/architecture_diagram.dendrite.yaml`](../../architecture_diagram.dendrite.yaml)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Repository: [`codebase/github-repo.md`](github-repo.md)
  - Apply Pipeline: [`codebase/gha-apply.md`](gha-apply.md)
  - WIF Pool: [`deployed_gcp_assets/wif-pool.md`](../deployed_gcp_assets/wif-pool.md)
  - State Bucket: [`deployed_gcp_assets/gcs-tfstate.md`](../deployed_gcp_assets/gcs-tfstate.md)
  - Terraform Modules: [`codebase/terraform-infrastructure-modules.md`](terraform-infrastructure-modules.md)
