---
okf_version: "1.0"
entry_id: "terraform-infrastructure-modules"
entry_name: "Terraform Infrastructure Modules"
category: "codebase"
sub_category: "terraform"
tier: "Tier 1 - Critical Path"
status: "active"
owner: "Cloud Platform Engineering / Academy L200"
dendrite_node_id: "github_repo"
discovered_by: "static_analysis"
last_verified: "2026-09-29"
---

# OKF (Codebase): Terraform Infrastructure Modules

## 1. Executive Summary & Purpose
- **Primary Function**: Declarative Infrastructure as Code (IaC) definitions managing Argolis GCP project resources (VPC networks, compute instances, security firewalls, and storage backends) using HashiCorp Terraform and Google Cloud Platform provider modules.
- **Target Audience / Consumer**: Cloud Infrastructure Engineers, automated GitHub Actions CI/CD pipelines (`terraform-plan.yml`, `terraform-apply.yml`), and Antigravity AI agents.
- **Key Outcome**: Standardizes reproducible cloud environments across sandboxes, ensuring all infrastructure modifications are version-controlled, plan-inspected during pull request review, and deployed via keyless CI/CD.

## 2. Codebase & Architectural Context
- **Mermaid Diagram Backing**:
  - Authoritative Platform: **Mermaid** (`docs/architecture_diagram.mmd`)
  - Node ID: `github_repo` (Source of truth and pipeline trigger)
  - Architectural Boundaries: `github_platform` (orchestration) and `argolis_project` (resource delivery)
- **Source Code Paths**:
  - Module directory: [`terraform/`](../../../terraform/)
  - Provider & Version Constraints: [`terraform/versions.tf`](../../../terraform/versions.tf) (`terraform >= 1.5.0`, `hashicorp/google ~> 6.0`)
  - Provider Initialization: [`terraform/provider.tf`](../../../terraform/provider.tf)
  - Input Variables: [`terraform/variables.tf`](../../../terraform/variables.tf)
  - Core Resources: [`terraform/main.tf`](../../../terraform/main.tf)
  - Declarative Import Blocks: [`terraform/imports.tf`](../../../terraform/imports.tf)
  - Remote State Backend: [`terraform/backend.tf`](../../../terraform/backend.tf)
  - Outputs: [`terraform/outputs.tf`](../../../terraform/outputs.tf)
  - Remote Backend Template: [`terraform/backend.tf.example`](../../../terraform/backend.tf.example)
  - Sample Variables: [`terraform/terraform.tfvars.example`](../../../terraform/terraform.tfvars.example)
- **Inbound Connections**:
  - PR Checks: `.github/workflows/terraform-plan.yml` validates and plans proposed modifications.
  - Automated Release: `.github/workflows/terraform-apply.yml` provisions approved changes upon merge.
  - Local Inspection: Cloudtop developer shell via `./bin/terraform plan`.
- **Outbound Connections**:
  - GCP Resource Manager & Compute APIs (`compute.googleapis.com`)
  - Remote State Storage: Google Cloud Storage bucket (`gs://<PROJECT_ID>-tfstate`)
- **Data & Control Flow**:
  - Runner assumes `github-terraform-deployer` SA via Workload Identity Federation (WIF) OIDC token.
  - Obtains remote state lock from GCS bucket, synchronizes `terraform.tfstate`, and executes declarative updates against the Argolis project.

## 3. Technical Specifications & Configuration
- **Input Variables**:
  | Variable | Type | Default | Required | Description |
  |---|---|---|---|---|
  | `project_id` | `string` | N/A | Yes | Target GCP project identifier |
  | `region` | `string` | `"us-central1"` | No | Default GCP region for regional resources |
  | `zone` | `string` | `"us-central1-a"` | No | Default GCP zone for compute engine VMs |
  | `manage_project_iam` | `bool` | `false` | No | Whether to manage project-level IAM bindings (requires projectIamAdmin) |
- **Remote State Backend**:
  ```hcl
  terraform {
    backend "gcs" {
      prefix = "terraform/state"
    }
  }
  ```
- **Security & IAM Roles**:
  - Execution Service Account: `github-terraform-deployer@<PROJECT_ID>.iam.gserviceaccount.com`
  - Required IAM Roles: `roles/compute.admin`, `roles/storage.admin`, `roles/iam.serviceAccountUser`
  - Zero long-lived keys: Workflows authenticate dynamically via WIF.

## 4. Operational Runbook & Lifecycle
- **Step 1: Local Linting & Validation**:
  ```bash
  cd terraform
  ../bin/terraform fmt -check
  ../bin/terraform init -backend=false
  ../bin/terraform validate
  ```
- **Step 2: CI/CD Pipeline Execution**:
  1. Open a pull request modifying `terraform/*.tf`.
  2. GitHub Actions executes `terraform-plan.yml`, generating a plan summary in the PR checks.
  3. Once merged into `main`, `terraform-apply.yml` acquires the GCS lock and applies changes.
- **Step 3: Failure Modes & Blast Radius**:
  - *Symptom*: `Error: Error acquiring the state lock`.
    - *Remediation*: If a preceding workflow crashed or was cancelled, inspect active locks in Cloud Storage:
      ```bash
      ../bin/terraform force-unlock <LOCK_ID>
      ```
  - *Symptom*: Plan drift between local and remote state.
    - *Remediation*: Always run `terraform refresh` against the remote GCS backend before local plan analysis.
  - *Symptom*: `Warning: Missing backend configuration` or `409 Conflict: Already exists`.
    - *Remediation*: Ensure `backend.tf` declares `backend "gcs" {}` and `imports.tf` contains declarative `import {}` blocks for existing cloud assets.

## 5. References & Cross-Links
- **Mermaid Diagram Nodes**: `github_repo`, `gha_plan`, `gha_apply`, `gcs_tfstate`, `vpc_network`, `compute_vm` in [`docs/architecture_diagram.mmd`](../../architecture_diagram.mmd)
- **Architecture Overview**: [`docs/architecture.md`](../../architecture.md)
- **Related OKF Entries**:
  - Canonical Component: [`components/github-repo.md`](github-repo.md)
  - Remote State Component: [`components/gcs-tfstate.md`](../deployed_gcp_assets/gcs-tfstate.md)
  - CI Pipeline Component: [`components/gha-plan.md`](gha-plan.md)
  - CD Pipeline Component: [`components/gha-apply.md`](gha-apply.md)
  - Deployed Compute Asset: [`deployed_gcp_assets/compute-instances.md`](../deployed_gcp_assets/compute-instances.md)
